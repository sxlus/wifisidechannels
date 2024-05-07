import pathlib

import wifisidechannels.units.wifi as wifi

class TxBf(wifi.WiFi):

    """
    @Job:   Decodes and Decompresses "VHT compressed beamfroming reports"

    """

    m_name: str = "[ txbf ]"

    def __init__(self, **kwargs):
        super().__init__(
            **(kwargs | 
                (
                    {
                            "name": self.m_name
                    } if not kwargs.get("name") else {}
                )
            )
        )


    def classify(self):
        """
        1D CNN with adversarial learning framework optimizing domain discriminator and value predictor.
        In its own class. Here interface with purpose.
        """
        pass

    def preprocess_data(self):
        """
        Does all that is necessary to prepare data for training.
        """
        pass

    def SRA(self):
        """
        Sparse recovery algorithm as proposed by Hu et. al. Autoencoder framework with 1D CNN.
        In its own class. Here interface with purpose.
        """
        pass

    def segment(self):
        """
        Segmentation of samples using Constant false alarm rate algorithm.
        """
        pass