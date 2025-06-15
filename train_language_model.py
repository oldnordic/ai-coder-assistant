# train_language_model.py
import os
from tokenizers import Tokenizer, models, pre_tokenizers, decoders, trainers
import torch
from torch.utils.data import Dataset, DataLoader
from torch.nn import TransformerEncoder, TransformerEncoderLayer, Linear, Embedding, CrossEntropyLoss
import math
import config

class PositionalEncoding(torch.nn.Module):
    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = torch.nn.Dropout(p=dropout)
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)

class TransformerModel(torch.nn.Module):
    def __init__(self, ntoken, d_model, nhead, d_hid, nlayers, dropout=0.5):
        super(TransformerModel, self).__init__()
        self.model_type = 'Transformer'
        self.pos_encoder = PositionalEncoding(d_model, dropout)
        encoder_layers = TransformerEncoderLayer(d_model, nhead, d_hid, dropout, batch_first=True, norm_first=True)
        self.transformer_encoder = TransformerEncoder(encoder_layers, nlayers)
        self.encoder = Embedding(ntoken, d_model, padding_idx=config.PAD_TOKEN_ID)
        self.d_model = d_model
        self.decoder = Linear(d_model, ntoken)
        self.init_weights()

    def init_weights(self):
        initrange = 0.1
        self.encoder.weight.data.uniform_(-initrange, initrange)
        self.decoder.bias.data.zero_()
        self.decoder.weight.data.uniform_(-initrange, initrange)

    def forward(self, src, src_mask=None):
        src = self.encoder(src) * math.sqrt(self.d_model)
        src = self.pos_encoder(src)
        output = self.transformer_encoder(src, src_mask)
        output = self.decoder(output)
        return output
    
    def generate(self, context_tensor, max_new_tokens):
        """
        Generates new tokens based on a starting context tensor.
        """
        self.eval() 
        with torch.no_grad():
            for _ in range(max_new_tokens):
                context_cond = context_tensor[:, -config.MAX_SEQUENCE_LENGTH:]
                logits = self(context_cond)
                logits = logits[:, -1, :]
                probs = torch.nn.functional.softmax(logits, dim=-1)
                idx_next = torch.multinomial(probs, num_samples=1)
                if idx_next.item() == config.PAD_TOKEN_ID:
                    break
                context_tensor = torch.cat((context_tensor, idx_next), dim=1)
        return context_tensor

class TextDataset(Dataset):
    def __init__(self, file_path, tokenizer, max_length):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.src = []
        self.tgt = []
        pad_token_id = config.PAD_TOKEN_ID
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines:
            encoded = self.tokenizer.encode(line).ids
            if len(encoded) < 2: continue
            if len(encoded) > self.max_length:
                processed_encoded = encoded[:self.max_length]
            else:
                padding = [pad_token_id] * (self.max_length - len(encoded))
                processed_encoded = encoded + padding
            self.src.append(torch.tensor(processed_encoded[:-1]))
            self.tgt.append(torch.tensor(processed_encoded[1:]))

    def __len__(self):
        return len(self.src)

    def __getitem__(self, idx):
        return self.src[idx], self.tgt[idx]

def train_model(vocab_dir, model_save_path, finetune=False, **kwargs):
    log_message_callback = kwargs.get('log_message_callback', print)
    progress_callback = kwargs.get('progress_callback', lambda c, t, m: None)

    try:
        device = config.DEVICE
        log_message_callback(f"Using device: {device}")
        
        training_data_path = config.FINETUNING_FILE_PATH if finetune and os.path.exists(config.FINETUNING_FILE_PATH) else config.CONCAT_FILE_PATH
        log_message_callback(f"Using training data: {os.path.basename(training_data_path)}")

        if not os.path.exists(training_data_path) or os.path.getsize(training_data_path) == 0:
            return "Error: Training data file not found or is empty. Please run pre-processing."

        tokenizer_path = os.path.join(vocab_dir, "tokenizer.json")
        if not os.path.exists(tokenizer_path):
            log_message_callback("Tokenizer not found. Training new one on general corpus.")
            tokenizer = Tokenizer(models.WordLevel(unk_token=config.UNK_TOKEN))
            tokenizer.pre_tokenizer = pre_tokenizers.Whitespace()
            trainer = trainers.WordLevelTrainer(vocab_size=config.VOCAB_SIZE, special_tokens=[config.UNK_TOKEN, config.PAD_TOKEN])
            tokenizer.train([config.CONCAT_FILE_PATH], trainer)
            tokenizer.save(tokenizer_path)
            log_message_callback(f"Tokenizer trained and saved to {tokenizer_path}")
        else:
            tokenizer = Tokenizer.from_file(tokenizer_path)

        dataset = TextDataset(training_data_path, tokenizer, config.MAX_SEQUENCE_LENGTH)
        dataloader = DataLoader(dataset, batch_size=config.BATCH_SIZE, shuffle=True)
        log_message_callback(f"Dataset prepared with {len(dataset)} samples.")

        ntokens = tokenizer.get_vocab_size()
        model = TransformerModel(ntokens, config.EMBED_DIM, config.NUM_HEADS, config.EMBED_DIM, config.NUM_LAYERS, config.DROPOUT).to(device)

        if finetune and os.path.exists(model_save_path):
            log_message_callback("Loading existing model weights for finetuning.")
            model.load_state_dict(torch.load(model_save_path, map_location=device))
        else:
            log_message_callback("Initializing new model for base training.")

        criterion = CrossEntropyLoss(ignore_index=config.PAD_TOKEN_ID)
        optimizer = optim.Adam(model.parameters(), lr=0.0005 if finetune else 0.001)

        log_message_callback(f"Starting model {'finetuning' if finetune else 'base training'} for {config.NUM_EPOCHS} epochs...")
        total_batches = len(dataloader)
        for epoch in range(config.NUM_EPOCHS):
            model.train()
            total_loss = 0
            for i, (src, tgt) in enumerate(dataloader):
                src, tgt = src.to(device), tgt.to(device)
                optimizer.zero_grad()
                output = model(src)
                loss = criterion(output.view(-1, ntokens), tgt.view(-1))
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 0.5)
                optimizer.step()
                total_loss += loss.item()
                current_progress = int(100 * (epoch / config.NUM_EPOCHS + (i + 1) / (total_batches * config.NUM_EPOCHS)))
                progress_callback(current_progress, 100, f"Epoch {epoch+1}/{config.NUM_EPOCHS}, Batch {i+1}/{total_batches}, Loss: {loss.item():.4f}")
            avg_loss = total_loss / len(dataloader)
            log_message_callback(f"Epoch {epoch+1}/{config.NUM_EPOCHS} | Average Loss: {avg_loss:.4f}")

        progress_callback(100, 100, "Saving model...")
        torch.save(model.state_dict(), model_save_path)
        log_message_callback(f"Model saved to {model_save_path}")
        return "Success"
    except Exception as e:
        log_message_callback(f"An error occurred during training: {e}")
        return f"Error: {e}"