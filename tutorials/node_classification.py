import os
import pathlib

import numpy as np
import torch
import torch_geometric.transforms as T
from torch_geometric.utils import to_dense_adj

from stable_gnn.explain import Explain
from stable_gnn.graph import Graph
from stable_gnn.pipelines.node_classification_pipeline import TrainModelNC, TrainModelOptunaNC

if __name__ == "__main__":
    name = "wisconsin"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    adjust_flag = False
    loss_name = "APP"  # APP, LINE, HOPE_AA, VERSE_Adj

    ssl_flag = True
    root = str(pathlib.Path(__file__).parent.resolve().joinpath("data_validation/")) + "/"

    dataset = Graph(name, root=root + str(name), transform=T.NormalizeFeatures(), adjust_flag=adjust_flag)
    data = dataset[0]

    optuna_training = TrainModelOptunaNC(data=dataset, device=device, ssl_flag=ssl_flag, loss_name=loss_name)

    best_values = optuna_training.run(number_of_trials=10)
    model_training = TrainModelNC(data=dataset, device=device, ssl_flag=ssl_flag, loss_name=loss_name)

    model, train_acc_mi, train_acc_ma, test_acc_mi, test_acc_ma = model_training.run(best_values)

    print(train_acc_mi, test_acc_mi)

    features = np.load(root + name + "/X.npy")
    if os.path.exists(root + name + "/A.npy"):
        adj_matrix = np.load(root + name + "/A.npy")
    else:
        adj_matrix = torch.squeeze(to_dense_adj(data.edge_index.cpu())).numpy()

    explainer = Explain(model=model, adj_matrix=adj_matrix, features=features)
    pgm_explanation = explainer.structure_learning(2)
    print("explanations is", pgm_explanation.nodes, pgm_explanation.edges)
