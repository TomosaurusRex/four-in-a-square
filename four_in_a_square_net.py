import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader, random_split
import pickle
import matplotlib.pyplot as plt


# Board strings are 36 chars: 9 sub-boards x 4 cells.
# Each char is encoded as a 4-value one-hot vector:
#   '0' -> [1,0,0,0]  (empty cell)
#   '1' -> [0,1,0,0]  (Red / AI piece)
#   '2' -> [0,0,1,0]  (White / player piece)
#   ' ' -> [0,0,0,1]  (missing sub-board slot)
# Total input size: 36 x 4 = 144
INPUT_SIZE = 144
MODEL_PATH = "board_dicts/four_in_a_square_model.pth"
SNAPSHOT_DIR = "board_dicts/snapshots"
BEST_MODEL_PATH = "board_dicts/four_in_a_square_best.pth"


def encode_board_string(board_str):
    vec = []
    for char in board_str:
        if char == ' ':
            vec.extend([0.0, 0.0, 0.0, 1.0])
        else:
            v = int(char)
            one_hot = [0.0, 0.0, 0.0, 0.0]
            one_hot[v] = 1.0
            vec.extend(one_hot)
    return vec


def load_and_encode_data(pkl_path, min_count=1):
    print(f"Reading data from {pkl_path}...")
    with open(pkl_path, "rb") as f:
        raw_data = pickle.load(f)
    print(f"  Raw boards: {len(raw_data):,}")

    X_list, Y_list, skipped = [], [], 0
    for board_str, (count, avg_score) in raw_data.items():
        if count < min_count:
            skipped += 1
            continue
        X_list.append(encode_board_string(board_str))
        Y_list.append([avg_score])

    print(f"  Loaded {len(X_list):,} boards (skipped {skipped:,} with count < {min_count})")
    return torch.tensor(X_list, dtype=torch.float32), torch.tensor(Y_list, dtype=torch.float32)


class FourInASquareNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.layer1 = nn.Linear(INPUT_SIZE, 256)
        self.dropout1 = nn.Dropout(0.2)
        self.layer2 = nn.Linear(256, 128)
        self.dropout2 = nn.Dropout(0.2)
        self.layer3 = nn.Linear(128, 64)
        self.output = nn.Linear(64, 1)
        self.activation = nn.LeakyReLU(0.01)

    def forward(self, x):
        x = self.activation(self.layer1(x))
        x = self.dropout1(x)
        x = self.activation(self.layer2(x))
        x = self.dropout2(x)
        x = self.activation(self.layer3(x))
        x = torch.sigmoid(self.output(x))
        return x


def train(model, train_loader, test_loader, device, epochs=300, learning_rate=0.001,
          early_stop_patience=15, min_delta=1e-4):
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    loss_fn = nn.MSELoss()
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.001)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=10)

    train_loss_history = []
    test_loss_history = []
    best_test_loss = float("inf")
    epochs_no_improve = 0

    print("\nStarting Training Loop...")
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for batch_X, batch_Y in train_loader:
            batch_X, batch_Y = batch_X.to(device), batch_Y.to(device)
            optimizer.zero_grad()
            loss = loss_fn(model(batch_X), batch_Y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        train_loss_history.append(avg_loss)

        test_loss = evaluate(model, test_loader, device)
        test_loss_history.append(test_loss)

        torch.save(model.state_dict(), os.path.join(SNAPSHOT_DIR, f"epoch_{epoch:04d}.pth"))

        if test_loss < best_test_loss - min_delta:
            best_test_loss = test_loss
            epochs_no_improve = 0
            torch.save(model.state_dict(), BEST_MODEL_PATH)
            improved_marker = " *"
        else:
            epochs_no_improve += 1
            improved_marker = ""

        if epoch % 10 == 0 or improved_marker:
            print(f"Epoch {epoch:4d} | Train: {avg_loss:.5f} | Test: {test_loss:.5f} | "
                  f"LR: {optimizer.param_groups[0]['lr']:.6f} | No improve: {epochs_no_improve}{improved_marker}")

        scheduler.step(test_loss)

        if epochs_no_improve >= early_stop_patience:
            print(f"\nEarly stopping at epoch {epoch} — no improvement for {early_stop_patience} epochs.")
            print(f"Best test loss: {best_test_loss:.5f} (saved to {BEST_MODEL_PATH})")
            break

    return train_loss_history, test_loss_history


def evaluate(model, loader, device):
    model.eval()
    loss_fn = nn.MSELoss()
    total_loss = 0
    with torch.no_grad():
        for batch_X, batch_Y in loader:
            batch_X, batch_Y = batch_X.to(device), batch_Y.to(device)
            total_loss += loss_fn(model(batch_X), batch_Y).item()
    model.train()
    return total_loss / len(loader)


if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    X, Y = load_and_encode_data("board_dicts/heuristic_boards_and_scores.pkl", min_count=1)

    dataset = TensorDataset(X, Y)
    train_size = int(len(dataset) * 0.8)
    test_size = len(dataset) - train_size
    generator = torch.Generator()
    generator.manual_seed(42)
    train_dataset, test_dataset = random_split(dataset, [train_size, test_size], generator=generator)

    train_loader = DataLoader(train_dataset, batch_size=128, shuffle=True, num_workers=4, pin_memory=True)
    test_loader = DataLoader(test_dataset, batch_size=128, shuffle=False, num_workers=4, pin_memory=True)

    net = FourInASquareNet().to(device)
    train_loss_history, test_loss_history = train(net, train_loader, test_loader, device)

    torch.save(net.state_dict(), MODEL_PATH)
    print(f"\nFinal model saved to {MODEL_PATH}")
    print(f"Best model (lowest test loss) saved to {BEST_MODEL_PATH}")
    print(f"Per-epoch snapshots saved to {SNAPSHOT_DIR}/")

    plt.figure()
    plt.plot(train_loss_history, label="Train Loss")
    plt.plot(test_loss_history, label="Test Loss")
    plt.title("Loss over epochs: train and test")
    plt.xlabel("Epochs")
    plt.ylabel("Loss (MSE)")
    plt.legend()
    plt.show()
