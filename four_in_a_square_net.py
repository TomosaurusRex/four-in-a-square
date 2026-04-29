import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader, random_split
import pickle
import matplotlib.pyplot as plt


# Board strings are 36 chars: 9 sub-boards × 4 cells.
# Empty slot = "    " (4 spaces) → encoded as [0,0,0] per char.
# '0' → [1,0,0], '1' → [0,1,0], '2' → [0,0,1]
# Total input size: 36 × 3 = 108
INPUT_SIZE = 108
MODEL_PATH = "board_dicts/four_in_a_square_model.pth"


def encode_board_string(board_str):
    vec = []
    for char in board_str:
        if char == ' ':
            vec.extend([0.0, 0.0, 0.0])
        else:
            v = int(char)
            one_hot = [0.0, 0.0, 0.0]
            one_hot[v] = 1.0
            vec.extend(one_hot)
    return vec


def load_and_encode_data(pkl_path, min_count=2):
    print(f"Reading data from {pkl_path}...")
    with open(pkl_path, "rb") as f:
        raw_data = pickle.load(f)

    X_list = []
    Y_list = []
    skipped = 0

    for board_str, (count, avg_score) in raw_data.items():
        if count < min_count:
            skipped += 1
            continue
        X_list.append(encode_board_string(board_str))
        Y_list.append([avg_score])

    print(f"Loaded {len(X_list)} boards (skipped {skipped} with count < {min_count})")
    return torch.tensor(X_list, dtype=torch.float32), torch.tensor(Y_list, dtype=torch.float32)


class FourInASquareNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.layer1 = nn.Linear(INPUT_SIZE, 128)
        self.layer2 = nn.Linear(128, 64)
        self.output = nn.Linear(64, 1)

    def forward(self, x):
        x = torch.relu(self.layer1(x))
        x = torch.relu(self.layer2(x))
        x = torch.sigmoid(self.output(x))
        return x


def train(model, train_loader, test_loader, device, epochs=200, learning_rate=0.001):
    loss_fn = nn.MSELoss()
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)

    train_loss_history = []
    test_loss_history = []

    print("\nStarting Training Loop...")
    for epoch in range(epochs):
        model.train()
        total_loss = 0

        for batch_X, batch_Y in train_loader:
            batch_X, batch_Y = batch_X.to(device), batch_Y.to(device)
            optimizer.zero_grad()
            y_pred = model(batch_X)
            loss = loss_fn(y_pred, batch_Y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        train_loss_history.append(avg_loss)

        if epoch % 50 == 0:
            avg_test_loss = evaluate(model, test_loader, device)
            test_loss_history.append(avg_test_loss)
            print(f"Epoch {epoch} | Train Loss: {avg_loss:.5f} | Test Loss: {avg_test_loss:.5f}")

    return train_loss_history, test_loss_history


def evaluate(model, loader, device):
    model.eval()
    loss_fn = nn.MSELoss()
    total_loss = 0

    with torch.no_grad():
        for batch_X, batch_Y in loader:
            batch_X, batch_Y = batch_X.to(device), batch_Y.to(device)
            predictions = model(batch_X)
            loss = loss_fn(predictions, batch_Y)
            total_loss += loss.item()

    model.train()
    return total_loss / len(loader)


if __name__ == "__main__":
    # 0. Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # 1. Load data from heuristic pkl
    X, Y = load_and_encode_data("board_dicts/heuristic_boards_and_scores.pkl", min_count=2)

    # 2. Split 80/20
    dataset = TensorDataset(X, Y)
    train_size = int(len(dataset) * 0.8)
    test_size = len(dataset) - train_size

    generator = torch.Generator()
    generator.manual_seed(42)
    train_dataset, test_dataset = random_split(dataset, [train_size, test_size], generator=generator)

    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

    # 3. Model
    net = FourInASquareNet().to(device)

    # 4. Train
    train_loss_history, test_loss_history = train(net, train_loader, test_loader, device)

    # 5. Save
    torch.save(net.state_dict(), MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")

    # 6. Plot
    plt.figure()
    plt.plot(range(len(train_loss_history)), train_loss_history, label="Train Loss")
    plt.plot(range(0, len(train_loss_history), 50), test_loss_history, label="Test Loss")
    plt.title("Loss over epochs: train and test")
    plt.xlabel("Epochs")
    plt.ylabel("Loss (MSE)")
    plt.legend()
    plt.show()
