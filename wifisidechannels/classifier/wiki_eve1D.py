import torch

class WIKI_EVE(torch.nn.Module):

    def __init__(
            self,
            conv_in_channels: int,
            conv_out_channels: int,
            conv_kernel_size: int,
            conv_stride: int,
            GF_output_size: int,
            GC_labels: int,
            GD_labels: int,
            lambda_domain: float = 0.5 # some thing like learning rate, gets multiplied with gradient
    ) -> None:

        super(WIKI_EVE, self).__init__()

        # feature extractor
        self.GF = torch.nn.Sequential(
            torch.nn.Conv1d(
                in_channels=conv_in_channels,
                out_channels=conv_out_channels,
                kernel_size=conv_kernel_size,
                stride=conv_stride
            ),
            torch.nn.ReLU(),
            torch.nn.AdaptiveAvgPool1d(
                output_size=GF_output_size*3
            ),
            torch.nn.Conv1d(
                in_channels=conv_out_channels,
                out_channels=conv_out_channels*2,
                kernel_size=conv_kernel_size,
                stride=conv_stride
            ),
            torch.nn.ReLU(),
            torch.nn.AdaptiveAvgPool1d(
                output_size=GF_output_size
            )
        )

        # classifier
        self.GC = torch.nn.Sequential(
            torch.nn.Linear(
                in_features=2*conv_out_channels*GF_output_size,
                out_features=int((2*conv_out_channels*GF_output_size))
            ),
            torch.nn.ReLU(),
            torch.nn.Linear(
                in_features=int((2*conv_out_channels*GF_output_size)),
                out_features=GC_labels
            ),
        )

        # domain discriminator
        self.GD = torch.nn.Sequential(
            gradient_reversal.GradientReversal(alpha=lambda_domain),
            torch.nn.Linear(
                in_features=2*conv_out_channels*GF_output_size,
                out_features=int((2*conv_out_channels*GF_output_size))
            ),
            torch.nn.ReLU(),
            torch.nn.Linear(
                in_features=int((2*conv_out_channels*GF_output_size)),
                out_features=GD_labels
            ),
        )

    def forward(self, x):
        #print(x.shape)
        x = self.GF(x)
        #print(x.shape)
        x = torch.flatten(x, 1)
        #print(x.shape)
        x_gc = self.GC(x)
        #print(x_gc.shape)
        x_gd = self.GD(x)
        #print(x_gd.shape)

        return x_gc, x_gd