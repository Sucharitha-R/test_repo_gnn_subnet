import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split
from torch_geometric.data import DataLoader
from pathlib import Path
import copy

from dataset import generate, load_dataset, save_results, generate_confusion
from gnn import MUTAG_Classifier, Classifier


########################################################################################################################
# [1.] Initialize all graphs ::: Structure, features and computed labels ===============================================
########################################################################################################################
graphs_nr = 1000
nodes_per_graph_nr = 20

#dataset, path = generate(graphs_nr,nodes_per_graph_nr) 
# Uncomment for load dataset from custom path and load model
path = 'graphs_2_19'
load_model = True
dataset = load_dataset(path)

train_dataset, test_dataset = train_test_split(dataset, test_size=0.2, random_state=42)

########################################################################################################################
# [2.] GNN training preparation: define the dataset of the graphs and the batch details ================================
########################################################################################################################
               
train_dataloader = DataLoader(
    train_dataset,
    batch_size=64,
    shuffle=True)


########################################################################################################################
# [3.] GNN training ====================================================================================================
########################################################################################################################


epoch_nr = 300

input_dim = 1
n_classes = 2
if load_model:
    checkpoint = torch.load(f"{path}/checkpoint/checkpoint.pth")
    model = checkpoint['model']
    opt = checkpoint['optimizer']
else:
    model = Classifier(input_dim, n_classes)
    opt = torch.optim.Adam(model.parameters(), lr = 0.001)

model.train()

for epoch in range(epoch_nr):
    epoch_loss = 0
    graph_idx = 0
    for data in train_dataloader:
        batch = []
        for i in range(data.y.size(0)):
            for j in range(nodes_per_graph_nr):
                batch.append(i)
        logits = model(data, torch.tensor(batch))
        loss = F.nll_loss(logits, data.y)

        opt.zero_grad()
        loss.backward()
        opt.step()

        epoch_loss += loss.detach().item()
        graph_idx += 1
    epoch_loss /= graph_idx
    print('Epoch {}, loss {:.4f}'.format(epoch, epoch_loss))

########################################################################################################################
# [4.] Prediction ======================================================================================================
########################################################################################################################

confusion_array = []
true_class_array = []
predicted_class_array = []
model.eval()
correct = 0
true_class_array = []
predicted_class_array = []
test_loss = 0

for data in test_dataset:
    batch = []
    for i in range(nodes_per_graph_nr):
        batch.append(0)

    output = model(data, torch.tensor(batch))
    predicted_class = output.max(dim=1)[1]
    true_class = data.y.item()
    loss = F.nll_loss(output, torch.tensor([data.y]))
    test_loss += loss
    confusion_array.append(generate_confusion(true_class, predicted_class))

    predicted_class_array = np.append(predicted_class_array, predicted_class)
    true_class_array = np.append(true_class_array, true_class)

    correct += predicted_class.eq(data.y).sum().item()

test_loss /= len(test_dataset)
confusion_matrix_gnn = confusion_matrix(true_class_array, predicted_class_array)
print("\nConfusion matrix:\n")
print(confusion_matrix_gnn)

counter = 0
for it, i in zip(predicted_class_array, range(len(predicted_class_array))):
    if it == true_class_array[i]:
        counter += 1

accuracy = counter/len(true_class_array) * 100 
print("Accuracy: {}%".format(accuracy))
print("Test loss {}".format(test_loss))
