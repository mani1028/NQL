import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
import json
import os

class MiniLMPlanner(nn.Module):
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2", num_actions=15, num_operators=10):
        super(MiniLMPlanner, self).__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        self.hidden_size = self.encoder.config.hidden_size
        
        # Heads (Decoupled from Schema Entities)
        self.action_head = nn.Linear(self.hidden_size, num_actions)
        self.operator_head = nn.Linear(self.hidden_size, num_operators)
        
        # Binary heads for query structure detection
        self.filter_head = nn.Linear(self.hidden_size, 1)
        self.sort_head = nn.Linear(self.hidden_size, 1)
        self.limit_head = nn.Linear(self.hidden_size, 1)

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.last_hidden_state[:, 0, :] # Use [CLS]
        
        return {
            "action": self.action_head(pooled_output),
            "operator": self.operator_head(pooled_output),
            "has_filter": torch.sigmoid(self.filter_head(pooled_output)),
            "has_sort": torch.sigmoid(self.sort_head(pooled_output)),
            "has_limit": torch.sigmoid(self.limit_head(pooled_output))
        }

    def save_model(self, path="nql/ml/models/planner_v2.pt"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.eval()
        
        import torch.backends.quantized
        if 'qnnpack' in torch.backends.quantized.supported_engines:
            torch.backends.quantized.engine = 'qnnpack'
        
        quantized_model = torch.quantization.quantize_dynamic(
            self.cpu(), 
            {torch.nn.Linear}, 
            dtype=torch.qint8
        )
        
        example_input = torch.randint(0, 1000, (1, 128))
        example_mask = torch.ones((1, 128))
        traced_model = torch.jit.trace(quantized_model, (example_input, example_mask), strict=False)
        
        traced_model.save(path)
        print(f"Phase 4 Quantized Model saved to {path}")

def get_tokenizer(model_name="sentence-transformers/all-MiniLM-L6-v2"):
    return AutoTokenizer.from_pretrained(model_name)
