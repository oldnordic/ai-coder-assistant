import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import json
import os
import math
from tqdm import tqdm
from . import config

class TextDataset(Dataset):
    def __init__(self, tokenized_chunks_filepath):
        self.data = []
        with open(tokenized_chunks_filepath, 'r', encoding='utf-8') as f:
            for line in f:
                self.data.append(torch.tensor(json.loads(line)["numerical_tokens"], dtype=torch.long))
    def __len__(self): return len(self.data)
    def __getitem__(self, idx): return self.data[idx][:-1], self.data[idx][1:]

class CoderAILanguageModel(nn.Module):
    def __init__(self, vocab_size, embed_dim, num_heads, num_layers, dropout, max_seq_len):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        encoder_layers = nn.TransformerEncoderLayer(d_model=embed_dim, nhead=num_heads, dropout=dropout, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_layers)
        self.fc_out = nn.Linear(embed_dim, vocab_size)

    def forward(self, src):
        embedded = self.embedding(src)
        output = self.transformer_encoder(embedded)
        return self.fc_out(output)

def train_language_model(progress_callback=None, log_message_callback=None):
    _log = log_message_callback if callable(log_message_callback) else print
    if not os.path.exists(config.VOCAB_FILE):
        _log("Error: Vocabulary file not found.")
        return

    with open(config.VOCAB_FILE, 'r') as f:
        vocab = json.load(f)
    
    dataset = TextDataset(config.TOKENIZED_CHUNKS_FILE)
    loader = DataLoader(dataset, batch_size=config.BATCH_SIZE, shuffle=True)
    
    model = CoderAILanguageModel(len(vocab), config.EMBED_DIM, config.NUM_HEADS, config.NUM_LAYERS, config.DROPOUT, config.CHUNK_SIZE)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters())

    for epoch in range(config.NUM_EPOCHS):
        total_loss = 0
        with tqdm(loader, desc=f"Epoch {epoch+1}/{config.NUM_EPOCHS}", disable=(progress_callback is not None)) as pbar:
            for inputs, targets in pbar:
                inputs, targets = inputs.to(device), targets.to(device)
                optimizer.zero_grad()
                outputs = model(inputs)
                loss = criterion(outputs.view(-1, len(vocab)), targets.view(-1))
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
                pbar.set_postfix(loss=loss.item())
        _log(f"Epoch {epoch+1} average loss: {total_loss / len(loader):.4f}")

    torch.save(model.state_dict(), config.MODEL_SAVE_PATH)
    _log(f"Model saved to {config.MODEL_SAVE_PATH}")