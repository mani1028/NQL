import torch
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from .model import MiniLMPlanner, get_tokenizer
from .dataset_gen import DatasetGenerator
import json
import os
import argparse

class SQLDataset(Dataset):
    def __init__(self, data_path, tokenizer, action_to_idx, operator_to_idx, max_len=128):
        with open(data_path, 'r') as f:
            self.data = json.load(f)
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.action_to_idx = action_to_idx
        self.operator_to_idx = operator_to_idx

    def __len__(self):
        return len(self.data)

    def __getitem__(self, item):
        sample = self.data[item]
        query = sample['query']
        plan = sample['plan']
        
        encoding = self.tokenizer(
            query,
            padding='max_length',
            truncation=True,
            max_length=self.max_len,
            return_tensors='pt'
        )
        
        action_idx = self.action_to_idx.get(plan['action'], 0)
        
        # Determine primary operator
        primary_op = "NONE"
        if plan['filters']:
            primary_op = plan['filters'][0].get('operator', '=')
        operator_idx = self.operator_to_idx.get(primary_op, 0)
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'action': torch.tensor(action_idx, dtype=torch.long),
            'operator': torch.tensor(operator_idx, dtype=torch.long),
            'has_filter': torch.tensor(1.0 if plan['filters'] else 0.0, dtype=torch.float),
            'has_sort': torch.tensor(1.0 if plan['sort'] else 0.0, dtype=torch.float),
            'has_limit': torch.tensor(1.0 if plan.get('limit', 0) > 0 else 0.0, dtype=torch.float)
        }

def train(dataset_path=None, skip_gen=False, epochs=10, batch_size=32):
    if dataset_path is None:
        if os.path.exists('nql/ml/data/extended_dataset.json'):
            dataset_path = 'nql/ml/data/extended_dataset.json'
        else:
            dataset_path = 'nql/ml/data/dataset.json'
    
    if not skip_gen and 'extended' not in dataset_path:
        print("Generating synthetic dataset...")
        gen = DatasetGenerator()
        gen.generate_dataset(10000)
    
    print(f"Loading dataset from {dataset_path}...")
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    
    actions = sorted(list(set(s['plan']['action'] for s in data)))
    
    # Extract all operators
    operators = set(["NONE"])
    for s in data:
        for f in s['plan']['filters']:
            if isinstance(f, dict) and 'operator' in f:
                operators.add(f['operator'])
    operators = sorted(list(operators))
    
    print(f"Found {len(actions)} actions and {len(operators)} operators.")
    
    action_to_idx = {a: i for i, a in enumerate(actions)}
    operator_to_idx = {o: i for i, o in enumerate(operators)}
    
    # Save mapping for inference
    os.makedirs('nql/ml/data', exist_ok=True)
    with open('nql/ml/data/mapping.json', 'w') as f:
        json.dump({'actions': actions, 'operators': operators}, f)

    tokenizer = get_tokenizer()
    dataset = SQLDataset(dataset_path, tokenizer, action_to_idx, operator_to_idx)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    print(f"Starting Phase 4 training for {epochs} epochs...")
    model = MiniLMPlanner(num_actions=len(actions), num_operators=len(operators))
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if torch.backends.mps.is_available(): # Mac Silicon
        device = torch.device("mps")
    
    print(f"Using device: {device}")
    model.to(device)
    
    optimizer = optim.AdamW(model.parameters(), lr=5e-5)
    criterion_cls = torch.nn.CrossEntropyLoss()
    criterion_reg = torch.nn.BCELoss()

    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for batch in loader:
            optimizer.zero_grad()
            
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            target_action = batch['action'].to(device)
            target_operator = batch['operator'].to(device)
            target_filter = batch['has_filter'].to(device)
            target_sort = batch['has_sort'].to(device)
            target_limit = batch['has_limit'].to(device)
            
            outputs = model(input_ids, attention_mask)
            
            loss_action = criterion_cls(outputs['action'], target_action)
            loss_operator = criterion_cls(outputs['operator'], target_operator)
            loss_filter = criterion_reg(outputs['has_filter'].squeeze(), target_filter)
            loss_sort = criterion_reg(outputs['has_sort'].squeeze(), target_sort)
            loss_limit = criterion_reg(outputs['has_limit'].squeeze(), target_limit)
            
            loss = loss_action + loss_operator + loss_filter + loss_sort + loss_limit
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss / len(loader):.4f}")

    model.save_model()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the nql ML Intent Planner")
    parser.add_argument("--dataset", type=str, default=None, help="Path to dataset.json")
    parser.add_argument("--skip-gen", action="store_true", help="Skip dataset generation")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for training")
    
    args = parser.parse_args()
    train(dataset_path=args.dataset, skip_gen=args.skip_gen, epochs=args.epochs, batch_size=args.batch_size)
