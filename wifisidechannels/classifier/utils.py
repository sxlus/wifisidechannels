import torch

def train_loop(dataloader, model, loss_fn, optimizer, batch_size):
    v = False
    size = len(dataloader.dataset)
    # Set the model to training mode - important for batch normalization and dropout layers
    # Unnecessary in this situation but added for best practices
    model.train()

    for batch, bfi_data in enumerate(dataloader):

        #y_domain = torch.zeros_like(y_label, dtype=torch.long)
        y_label = torch.Tensor(bfi_data["label"])
        y_domain = torch.Tensor(bfi_data["domain"])
        #y_label = torch.nn.functional.one_hot(y_label.long(), num_classes=2).type(torch.float)
        #y_domain = torch.nn.functional.one_hot(y_domain.long(), num_classes=3).type(torch.float)
        X = torch.Tensor(bfi_data["data"])
        #X, y_label, y_domain = X.to(torch.device(device=device)), y_label.to(torch.device(device=device)), y_domain.to(torch.device(device=device))
        #X = X - torch.mean(X)
        # Compute prediction and loss
        pred = model(X)

        if v:
            print(pred[0].shape)
            print(pred[0])
            print(type((pred[0][0][0])), pred[1][0])
            print(pred[1].shape)
            print(y_label, type(y_label[0]), y_domain)
            print(y_label.shape, y_domain.shape)

        loss = loss_fn(pred[0], y_label, pred[1], y_domain)

        # Backpropagation
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

        if batch % 100 == 0:
            loss, current = loss.item(), batch * batch_size + len(X)
            print(f"loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")


def test_loop(dataloader, model, loss_fn):
    # Set the model to evaluation mode - important for batch normalization and dropout layers
    # Unnecessary in this situation but added for best practices
    v = False
    model.eval()
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    test_loss, correct, correct_label, correct_domain = 0, 0, 0, 0

    # Evaluating the model with torch.no_grad() ensures that no gradients are computed during test mode
    # also serves to reduce unnecessary gradient computations and memory usage for tensors with requires_grad=True
    with torch.no_grad():
        for batch, bfi_data in enumerate(dataloader):
            #y_domain = torch.zeros_like(y_label, dtype=torch.long)
            #X = X - torch.mean(X)
            y_label = torch.Tensor(bfi_data["label"])
            y_domain = torch.Tensor(bfi_data["domain"])
            #print(y_domain)
            #y_domain = torch.nn.functional.one_hot(y_domain.long(), num_classes=3).type(torch.float)
            #y_label = torch.nn.functional.one_hot(y_label.long(), num_classes=2).type(torch.float)
            X = torch.Tensor(bfi_data["data"])
            #X, y_label, y_domain = X.to(torch.device(device=device)), y_label.to(torch.device(device=device)), y_domain.to(torch.device(device=device))
            pred = model(X)
            if v:
                print(pred[1].shape, y_domain.shape, pred[0].shape, y_label.shape)
            test_loss += loss_fn(pred[0], y_label, pred[1], y_domain).item()
            #print(pred[0].argmax(1))
            #print(y_label)
            #correct += (((pred[0].argmax(1) == y_label) & (pred[1].argmax(1) == y_domain))).type(torch.float).sum().item()
            correct_label += ((pred[0].argmax(1) == y_label)).type(torch.float).sum().item()
            correct_domain += ((pred[1].argmax(1) == y_domain)).type(torch.float).sum().item()

    test_loss /= num_batches
    #correct /= size
    correct_label  /= size
    correct_domain /= size
    print(f"\n* Test Error: \n Accuracy (all): {(100*correct):>0.1f}%, Accuracy (label): {(100*correct_label):>0.1f}%, Accuracy (domain): {(100*correct_domain):>0.1f}%, Avg loss: {test_loss:>8f} \n")