import torch


class DraftPicker(torch.nn.Module):
    def __init__(self, input_dim: int, transformer_encoder_n_layers: int, transformer_encoder_layer_dim: int, transformer_encoder_layer_n_heads: int):
        super().__init__()
        self.input_dim = input_dim
        self.transformer_encoder_n_layers = transformer_encoder_n_layers
        self.transformer_encoder_layer_dim = transformer_encoder_layer_dim
        self.transformer_encoder_layer_n_heads = transformer_encoder_layer_n_heads

        # Initialize modules
        self.input_mlp = torch.nn.Sequential(
            torch.nn.Linear(
                in_features=self.input_dim,
                out_features=self.transformer_encoder_layer_dim
            ),
            torch.nn.ReLU()
        )
        self.transformer_encoder = torch.nn.TransformerEncoder(
            encoder_layer=torch.nn.TransformerEncoderLayer(
                d_model=self.transformer_encoder_layer_dim,
                nhead=self.transformer_encoder_layer_n_heads
            ),
            num_layers=self.transformer_encoder_n_layers
        )
        self.output_mlp = torch.nn.Sequential(
            torch.nn.Linear(
                in_features=self.transformer_encoder_layer_dim,
                out_features=1
            ),
        )

    def forward(self, x):
        x = self.input_mlp(x)
        x = self.transformer_encoder(x)
        y_logits = self.output_mlp(x)[..., 0]
        return y_logits
