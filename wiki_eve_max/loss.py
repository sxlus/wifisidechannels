import torch


class AdvLernLoss(torch.nn.Module):

    def __init__(self):
        super(AdvLernLoss, self).__init__()

    def forward(self, pred_label, targ_label, pred_domain, targ_domain, alpha=0.3):
        # ~74%
        #print("TARG", targ_label.shape, targ_label[:5])
        #print("TARG", targ_domain.shape, targ_domain[:5])
        #print("PRED", pred_label.shape, pred_label[:5])
        #print("PRED", pred_domain.shape, pred_domain[:5])

        label_loss = torch.nn.CrossEntropyLoss()(pred_label, targ_label)
        domain_loss = torch.nn.CrossEntropyLoss()(pred_domain, targ_domain)

        # the paper suggests these instead
        # inputs are messy
        #label_loss = torch.nn.BCEWithLogitsLoss()(pred_label, targ_label)
        #domain_loss = torch.nn.BCELoss()(pred_domain, targ_domain)
        #print("LOSS", label_loss, domain_loss)

        return label_loss + domain_loss

class OrdinaryLoss(torch.nn.Module):

    def __init__(self):
        super(OrdinaryLoss, self).__init__()

    def forward(self, pred_label, targ_label, pred_domain, targ_domain, alpha=0.3):
        # ~74%
        label_loss = torch.nn.CrossEntropyLoss()(pred_label, targ_label)
        #domain_loss = torch.nn.CrossEntropyLoss()(pred_domain, targ_domain)

        # the paper suggests these instead
        # inputs are messy
        #label_loss = torch.nn.BCEWithLogitsLoss()(pred_label, targ_label)
        #domain_loss = torch.nn.BCELoss()(pred_domain, targ_domain)
        #print(label_loss, domain_loss)

        return label_loss# + domain_loss