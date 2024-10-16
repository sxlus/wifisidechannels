import gradient_reversal
import torch

class WIKI_EVE_1D(torch.nn.Module):

    def __init__(
            self,
            conv_in_channels: int,
            conv_out_channels: int,
            conv_kernel_size: int,
            conv_stride: int,
            GF_output_size: int,
            GC_labels: int,
            GD_labels: int,
            groups: int,
            lambda_domain: float = 1e-6
    ) -> None:

        super(WIKI_EVE_1D, self).__init__()

        # feature extractor
        self.GF = torch.nn.Sequential(
            torch.nn.Conv1d(
                in_channels=conv_in_channels,
                out_channels=conv_out_channels,
                kernel_size=conv_kernel_size,
                stride=conv_stride,
                groups=groups
            ),
            torch.nn.ReLU(),
            torch.nn.AdaptiveMaxPool1d(
                output_size=GF_output_size*3
            ),
            torch.nn.Conv1d(
                in_channels=conv_out_channels,
                out_channels=conv_out_channels,
                kernel_size=conv_kernel_size,
                stride=conv_stride,
                groups=groups
            ),
            torch.nn.ReLU(),
            torch.nn.AdaptiveMaxPool1d(
                output_size=GF_output_size
            )
        )

        # classifier
        self.GC = torch.nn.Sequential(
            torch.nn.Linear(
                in_features=conv_out_channels*GF_output_size,
                out_features=1000
            ),
            torch.nn.ReLU(),
            torch.nn.Linear(
                in_features=1000,
                out_features=1000
            ),
            torch.nn.ReLU(),
            torch.nn.Linear(
                in_features=1000,
                out_features=GC_labels
            ),
            #torch.nn.Softmax()
        )

        # domain discriminator
        self.GD = torch.nn.Sequential(
            #broken ? :) 
            #gradient_reversal.GradientReversal(alpha=lambda_domain),
            torch.nn.Linear(
                in_features=conv_out_channels*GF_output_size,
                out_features=100
            ),
            torch.nn.ReLU(),
            torch.nn.Linear(
                in_features=100,
                out_features=GD_labels
            ),
            torch.nn.Sigmoid()
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
    

class WIKI_EVE_2D(torch.nn.Module):

    def __init__(
            self,
            conv_in_channels: int,
            conv_out_channels: int,
            conv_kernel_size: int,
            conv_stride: int,
            GF_output_size: int,
            GC_labels: int,
            GD_labels: int,
            lambda_domain: float = 0.5
    ) -> None:

        super(WIKI_EVE_2D, self).__init__()

        # feature extractor
        self.GF = torch.nn.Sequential(
            torch.nn.Conv2d(
                in_channels=conv_in_channels,
                out_channels=conv_out_channels,
                kernel_size=conv_kernel_size,
                stride=conv_stride
            ),
            torch.nn.ReLU(),
            torch.nn.AdaptiveMaxPool2d(
                output_size=GF_output_size*3
            ),
            torch.nn.Conv2d(
                in_channels=conv_out_channels,
                out_channels=conv_out_channels*2,
                kernel_size=conv_kernel_size,
                stride=conv_stride
            ),
            torch.nn.ReLU(),
            torch.nn.AdaptiveMaxPool2d(
                output_size=GF_output_size
            )
        )

        # classifier
        self.GC = torch.nn.Sequential(
            torch.nn.Linear(
                in_features=2*conv_out_channels*(GF_output_size**2),
                out_features=100
            ),
            torch.nn.ReLU(),
            torch.nn.Linear(
                in_features=100,
                out_features=100
            ),
            torch.nn.ReLU(),
            torch.nn.Linear(
                in_features=100,
                out_features=GC_labels
            ),
            #torch.nn.Softmax()
        )

        # domain discriminator
        self.GD = torch.nn.Sequential(
            gradient_reversal.GradientReversal(alpha=lambda_domain),
            torch.nn.Linear(
                in_features=2*conv_out_channels*(GF_output_size**2),
                out_features=100
            ),
            torch.nn.ReLU(),
            torch.nn.Linear(
                in_features=100,
                out_features=GD_labels
            ),
            torch.nn.Sigmoid()
        )

    def forward(self, x):
        #print(x.shape)
        x = self.GF(x)
        print(x.shape)
        x = torch.flatten(x, 1)
        print(x.shape)
        x_gc = self.GC(x)
        #print(x_gc.shape)
        x_gd = self.GD(x)
        #print(x_gd.shape)

        return x_gc, x_gd