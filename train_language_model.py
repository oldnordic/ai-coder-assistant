# train_language_model.py
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import json
import os
import config #

class TextDataset(Dataset):
    """A memory-efficient dataset for loading tokenized text line by line."""
    def __init__(self, tokenized_chunks_filepath):
        self.filepath = tokenized_chunks_filepath
        self.line_offsets = [] #
        
        # Open the file once to get all line offsets
        with open(self.filepath, 'r', encoding='utf-8') as f: #
            offset = 0 #
            while True: #
                line = f.readline() #
                if not line: # EOF reached
                    break #
                if line.strip(): # Only store offset for non-empty lines
                    self.line_offsets.append(offset) #
                offset = f.tell() # Get offset for the next line

        if not self.line_offsets: #
            raise ValueError(f"No valid lines found in tokenized chunks file: {self.filepath}") #

        # Load vocab to get PAD_TOKEN_ID for padding
        if not os.path.exists(config.VOCAB_FILE): #
            raise FileNotFoundError(f"Vocabulary file not found: {config.VOCAB_FILE}") #
        with open(config.VOCAB_FILE, 'r', encoding='utf-8') as f: #
            vocab = json.load(f) #
            # Use getattr for PAD_TOKEN_ID as it's set dynamically in preprocess_docs
            self.pad_token_id = getattr(config, 'PAD_TOKEN_ID', vocab.get(getattr(config, 'PAD_TOKEN', '<pad>'), 1)) # Use 1 as fallback default
        
        # Ensure MAX_SEQUENCE_LENGTH is defined in config.py
        self.max_seq_len = getattr(config, 'MAX_SEQUENCE_LENGTH', 256) #


    def __len__(self): #
        return len(self.line_offsets) #

    def __getitem__(self, idx): #
        with open(self.filepath, 'r', encoding='utf-8') as f: #
            f.seek(self.line_offsets[idx]) #
            line = f.readline() #
            tokens = json.loads(line)["numerical_tokens"] #
            
            # Trim or pad tokens to MAX_SEQUENCE_LENGTH
            if len(tokens) > self.max_seq_len: #
                tokens = tokens[:self.max_seq_len] #
            else: #
                tokens = tokens + [self.pad_token_id] * (self.max_seq_len - len(tokens)) #

            tensor = torch.tensor(tokens, dtype=torch.long) #
            
            # Ensure input and target are aligned after padding
            # For language modeling, target is shifted version of input
            # tensor[:-1] provides input, tensor[1:] provides target (shifted by one token)
            return tensor[:-1], tensor[1:] #

class CoderAILanguageModel(nn.Module): #
    """A simple Transformer-based language model.""" #
    def __init__(self, vocab_size, embed_dim, num_heads, num_layers, dropout): #
        super().__init__() #
        self.embedding = nn.Embedding(vocab_size, embed_dim) #
        encoder_layers = nn.TransformerEncoderLayer(d_model=embed_dim, nhead=num_heads, dropout=dropout, batch_first=True) #
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_layers) #
        self.fc_out = nn.Linear(embed_dim, vocab_size) #

    def forward(self, src): #
        embedded = self.embedding(src) #
        output = self.transformer_encoder(embedded) #
        return self.fc_out(output) #

def get_best_device(_log): #
    """
    Checks for available hardware accelerators and returns the best device.
    Priority: NVIDIA (CUDA) / AMD (ROCm) -> Apple (MPS) -> CPU.
    """ #
    # PyTorch uses 'cuda' for both NVIDIA and AMD ROCm builds.
    # We can add a check to see which one it is for clearer logging.
    if torch.cuda.is_available(): #
        device = torch.device("cuda") #
        try: #
            device_name = torch.cuda.get_device_name(0) #
            if "nvidia" in device_name.lower(): #
                _log(f"NVIDIA CUDA GPU detected: {device_name}. Using 'cuda' device.") #
            elif "amd" in device_name.lower(): #
                _log(f"AMD ROCm GPU detected: {device_name}. Using 'cuda' device (ROCm backend).") #
            else: #
                 _log(f"CUDA-compatible GPU detected: {device_name}. Using 'cuda' device.") #
        except Exception as e: #
            _log(f"CUDA device found, but could not get name. Error: {e}") #
        return device #

    # Check for Apple Metal Performance Shaders (MPS) for M1/M2/M3 chips
    if torch.backends.mps.is_available(): #
        device = torch.device("mps") #
        _log("Apple Metal (MPS) GPU detected. Using 'mps' device.") #
        return device #
    
    # Fallback to CPU
    device = torch.device("cpu") #
    _log("No compatible GPU detected. Falling back to CPU.") #
    return device #

def train_language_model(progress_callback=None, log_message_callback=None): #
    _log = log_message_callback if callable(log_message_callback) else print #
    
    if not os.path.exists(config.VOCAB_FILE) or not os.path.exists(config.TOKENIZED_CHUNKS_FILE): #
        _log("Error: Vocabulary or tokenized chunks file not found. Please run preprocessing first.") #
        if progress_callback: #
            progress_callback(1, 1, "Error: Missing data files.") #
        return #

    with open(config.VOCAB_FILE, 'r') as f: #
        vocab = json.load(f) #
    
    _log("Initializing dataset...") #
    try: #
        # The TextDataset constructor now handles loading pad_token_id and max_seq_len
        dataset = TextDataset(config.TOKENIZED_CHUNKS_FILE) #
    except Exception as e: #
        _log(f"Error initializing dataset: {e}") #
        return #
        
    if len(dataset) == 0: #
        _log("Error: No data found in tokenized chunks file. Cannot train."); return #
        
    loader = DataLoader(dataset, batch_size=config.BATCH_SIZE, shuffle=True) #
    
    device = get_best_device(_log) #
    
    # vocab_size should be len(vocab) loaded in TextDataset or directly here for model init
    model = CoderAILanguageModel(len(vocab), config.EMBED_DIM, config.NUM_HEADS, config.NUM_LAYERS, config.DROPOUT) #
    model.to(device) #
    
    # Use ignore_index for the padding token in loss calculation
    criterion = nn.CrossEntropyLoss(ignore_index=getattr(config, 'PAD_TOKEN_ID', 1)) #
    optimizer = optim.Adam(model.parameters()) #

    num_epochs = config.NUM_EPOCHS #
    num_batches = len(loader) #
    total_steps = num_epochs * num_batches #

    _log(f"Starting training for {num_epochs} epochs on device '{device}'...") #
    for epoch in range(num_epochs): #
        model.train() #
        total_loss = 0 #
        for i, (inputs, targets) in enumerate(loader): #
            inputs, targets = inputs.to(device), targets.to(device) #
            
            optimizer.zero_grad() #
            outputs = model(inputs) #
            # outputs: (batch_size, seq_len, vocab_size)
            # targets: (batch_size, seq_len)
            loss = criterion(outputs.view(-1, len(vocab)), targets.view(-1)) #
            loss.backward() #
            optimizer.step() #
            
            total_loss += loss.item() #
            
            if progress_callback: #
                current_step = epoch * num_batches + i + 1 #
                progress_callback(current_step, total_steps, f"Epoch {epoch+1}/{num_epochs}, Batch {i+1}/{num_batches}") #

        avg_loss = total_loss / num_batches if num_batches > 0 else 0 #
        _log(f"Epoch {epoch+1} average loss: {avg_loss:.4f}") #

    # Ensure the directory for saving the model exists
    os.makedirs(os.path.dirname(config.MODEL_SAVE_PATH), exist_ok=True) #
    torch.save(model.state_dict(), config.MODEL_SAVE_PATH) #
    _log(f"Model saved to {config.MODEL_SAVE_PATH}") #
    if progress_callback: #
        progress_callback(total_steps, total_steps, "Training complete!") #