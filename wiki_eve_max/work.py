import torch
import typing

def train_loop(dataloader, model, loss_fn, optimizer, batch_size, datakind = "bfi", device = None, v = False, batch_no_print = 1000):
    size = len(dataloader.dataset)
    # Set the model to training mode - important for batch normalization and dropout layers
    # Unnecessary in this situation but added for best practices
    model.train()

    for batch, data in enumerate(dataloader):
        if datakind == "bfi":
            X = torch.Tensor(data["data"])
            y_label = torch.Tensor(data["label"]).long()
            y_domain =  torch.zeros_like(y_label, dtype=torch.long) # torch.Tensor(data["domain"]).long()
        else:
            X = data[0]
            if len(data[1]) != len(X):
                y_label = data[1][0]
                y_domain = data[1][1]
            else:
                y_label = data[1]
                y_domain = torch.zeros_like(y_label, dtype=torch.long)
            #y_label = torch.nn.functional.one_hot(y_label.long(), num_classes=10).type(torch.float)
            #y_domain = torch.nn.functional.one_hot(y_domain.long(), num_classes=10).type(torch.float)

        #print(len(X), X[:22])
        #print(len(y_label), y_label[:22])
        #print(len(y_domain), y_domain[:22])
        #print(device)
        if device is not None:
            X, y_label, y_domain = X.to(torch.device(device=device)), y_label.to(torch.device(device=device)), y_domain.to(torch.device(device=device))

        pred_label, pred_domain = model(X)
        if v:
                print("PRED LABEL: ", type(pred_label), pred_label.shape, pred_label[0], pred_label.argmax(1))
                print("TARG LABEL: ", type(y_label), y_label.shape, y_label)
                print("\n\n\n")
                print("PRED DOMAIN: ", type(pred_domain), pred_domain.shape, pred_domain[0], pred_domain.argmax(1))
                print("TARG DOMAIN: ", type(y_domain), y_domain.shape, y_domain)
                print("\n\n\n")


        loss = loss_fn(pred_label, y_label, pred_domain, y_domain)

        # Backpropagation
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

        
        if batch % batch_no_print == 0:
            loss, current = loss.item(), batch * batch_size + len(X)
            print(f"loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")


def test_loop(dataloader, model, loss_fn, datakind = "bfi", device = None, v = False, batch_no_print = None, no_batches = None):
    # Set the model to evaluation mode - important for batch normalization and dropout layers
    # Unnecessary in this situation but added for best practices
    model.eval()
    size = len(dataloader.dataset) if no_batches is None else no_batches*dataloader.batch_size
    num_batches = len(dataloader) if no_batches is None else no_batches
    test_loss, correct, correct_label, correct_domain = 0, 0, 0, 0

    # Evaluating the model with torch.no_grad() ensures that no gradients are computed during test mode
    # also serves to reduce unnecessary gradient computations and memory usage for tensors with requires_grad=True
    with torch.no_grad():
        for batch, data in enumerate(dataloader):
            if isinstance(no_batches, int):
                if batch == no_batches-1:
                    break
            if datakind == "bfi":
                X = torch.Tensor(data["data"])
                y_label  = torch.Tensor(data["label"]).long()
                y_domain =  torch.zeros_like(y_label, dtype=torch.long) # torch.Tensor(data["domain"]).long()
            else:
                X = data[0]
                if len(data[1]) != len(X):
                    y_label = data[1][0]
                    y_domain = data[1][1]
                else:
                    y_label = data[1]
                    y_domain = torch.zeros_like(y_label, dtype=torch.long)
                #y_label = torch.nn.functional.one_hot(y_label.long(), num_classes=10).type(torch.float)
                #y_domain = torch.nn.functional.one_hot(y_domain.long(), num_classes=10).type(torch.float)

            if device is not None:
                X, y_label, y_domain = X.to(torch.device(device=device)), y_label.to(torch.device(device=device)), y_domain.to(torch.device(device=device))

            pred_label, pred_domain = model(X)
            if v:
                print("PRED LABEL: ", type(pred_label), pred_label.shape, pred_label[0], pred_label.argmax(1))
                print("TARG LABEL: ", type(y_label), y_label.shape, y_label)
                print("\n\n\n")
                print("PRED DOMAIN: ", type(pred_domain), pred_domain.shape, pred_domain[0], pred_domain.argmax(1))
                print("TARG DOMAIN: ", type(y_domain), y_domain.shape, y_domain)
            test_loss += loss_fn(pred_label, y_label, pred_domain, y_domain).item()
            correct_label += ((pred_label.argmax(1) == y_label)).type(torch.int).sum().item()
            correct_domain += ((pred_domain.argmax(1) == y_domain)).type(torch.int).sum().item()
            if isinstance(batch_no_print, int):
                if batch % batch_no_print == 0 and batch != 0:
                    tmp_test_loss = test_loss / (batch+1)
                    tmp_correct_label  = correct_label / ((batch+1)*dataloader.batch_size)
                    tmp_correct_domain = correct_domain / ((batch+1)*dataloader.batch_size)
                    print(f"\n* Test Error: \n Accuracy (label): {(100*tmp_correct_label):>0.1f}%, Accuracy (domain): {(100*tmp_correct_domain):>0.1f}%, Avg loss: {tmp_test_loss:>8f} \n")


    test_loss /= num_batches
    correct_label  /= size
    correct_domain /= size
    print(f"\n* Test Error: \n Accuracy (label): {(100*correct_label):>0.1f}%, Accuracy (domain): {(100*correct_domain):>0.1f}%, Avg loss: {test_loss:>8f} \n")
