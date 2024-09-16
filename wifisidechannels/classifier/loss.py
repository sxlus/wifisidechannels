import torch

class AdvLernLoss(torch.nn.Module):

    def __init__(self):
        super(AdvLernLoss, self).__init__()

    def forward(self, pred_label, targ_label, pred_domain, targ_domain, alpha=0.3):
        # ~74%
        label_loss = torch.nn.CrossEntropyLoss()(pred_label, targ_label)
        domain_loss = torch.nn.CrossEntropyLoss()(pred_domain, targ_domain)

        # the paper suggests these instead
        # inputs are messy
        #label_loss = torch.nn.BCEWithLogitsLoss()(pred_label, targ_label)
        #domain_loss = torch.nn.BCELoss()(pred_domain, targ_domain)
        #print(label_loss, domain_loss)

        return label_loss + domain_loss