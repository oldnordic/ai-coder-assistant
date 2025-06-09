import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import json
import os
import config

class TextDataset(Dataset):
    def __init__(self, tokenized_chunks_filepath):
        self.filepath = tokenized_chunks_filepath
        self.line_offsets = []
        with open(self.filepath, 'r', encoding='utf-8') as f:
            offset = 0
            for line in f:
                self.line_offsets.append(offset)
                offset += len(line.encode('utf-8'))

    def __len__(self):
        return len(self.line_offsets)

    def __getitem__(self, idx):
        with open(self.filepath, 'r', encoding='utf-8') as f:
            f.seek(self.line_offsets[idx])
            line = f.readline()
            tokens = json.loads(line)["numerical_tokens"]
            tensor = torch.tensor(tokens, dtype=torch.long)
            return tensor[:-1], tensor[1:]

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
    
    if not os.path.exists(config.VOCAB_FILE) or not os.path.exists(config.TOKENIZED_CHUNKS_FILE):
        _log("Error: Vocabulary or tokenized chunks file not found. Please run preprocessing first.")
        if progress_callback:
            progress_callback(1, 1, "Error: Missing data files.")
        return

    with open(config.VOCAB_FILE, 'r') as f:
        vocab = json.load(f)
    
    _log("Initializing memory-efficient dataset...")
    try:
        dataset = TextDataset(config.TOKENIZED_CHUNKS_FILE)
    except Exception as e:
        _log(f"Error initializing dataset: {e}")
        return
        
    if len(dataset) == 0:
        _log("Error: No data found in tokenized chunks file. Cannot train.")
        if progress_callback:
            progress_callback(1, 1, "Error: No data to train on.")
        return
        
    loader = DataLoader(dataset, batch_size=config.BATCH_SIZE, shuffle=True)
    
    model = CoderAILanguageModel(len(vocab), config.EMBED_DIM, config.NUM_HEADS, config.NUM_LAYERS, config.DROPOUT, config.CHUNK_SIZE)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _log(f"Training on device: {device}")
    model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters())

    num_epochs = config.NUM_EPOCHS
    num_batches = len(loader)
    total_steps = num_epochs * num_batches

    _log(f"Starting training for {num_epochs} epochs...")
    for epoch in range(num_epochs):
        total_loss = 0
        for i, (inputs, targets) in enumerate(loader):
            inputs, targets = inputs.to(device), targets.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs.view(-1, len(vocab)), targets.view(-1))
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
            if progress_callback:
                current_step = epoch * num_batches + i + 1
                progress_callback(current_step, total_steps, f"Epoch {epoch+1}/{num_epochs}, Batch {i+1}/{num_batches}")

        avg_loss = total_loss / num_batches if num_batches > 0 else 0
        _log(f"Epoch {epoch+1} average loss: {avg_loss:.4f}")

    torch.save(model.state_dict(), config.MODEL_SAVE_PATH)
    _log(f"Model saved to {config.MODEL_SAVE_PATH}")
    if progress_callback:
        progress_callback(total_steps, total_steps, "Training complete!")