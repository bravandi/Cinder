import communication
import numpy as np
import pdb
from sklearn import tree
# from tableausdk import *

def iris_demo():

    from sklearn.datasets import load_iris
    from sklearn import tree
    iris = load_iris()
    clf = tree.DecisionTreeClassifier()
    clf = clf.fit(iris.data, iris.target)

    # with open("iris.dot", 'w') as f:
    #     f = tree.export_graphviz(clf, out_file=f)

    # import os
    # os.unlink('iris.dot')

    import pydotplus
    # dot_data = tree.export_graphviz(clf, out_file=None)
    # graph = pydotplus.graph_from_dot_data(dot_data)
    # graph.write_pdf("iris.pdf")

    dot_data = tree.export_graphviz(clf, out_file=None,
                             feature_names=iris.feature_names,
                             class_names=iris.target_names,
                             filled=True, rounded=True,
                             special_characters=True)

    graph = pydotplus.graph_from_dot_data(dot_data)

    png = graph.create_png()

    fh = open("imageToSave.png", "wb")
    fh.write(png)
    fh.close()


def prepare_traning_dataset(result_set, target_column, ignore_columns=[]):
    columns = {}

    cut_columns_indexes = []
    ignore_cut_columns_indexes = []

    for column in result_set[0]:

        columns[column] = result_set[0].index(column)

        if column == target_column:
            cut_columns_indexes.append(columns[column])

        if column in ignore_columns:
            ignore_cut_columns_indexes.append(columns[column])

    cut1 = []
    cut2 = []

    ignore_cut_columns_indexes.extend(cut_columns_indexes)

    feature_names = [
        feature.encode('ascii', 'ignore')
        for feature in np.delete(np.array(result_set[0]), ignore_cut_columns_indexes).tolist()]

    for row in result_set[1:]:
        a = np.array(row)

        cut1.append(np.delete(a, ignore_cut_columns_indexes).tolist())
        # cut2.append(a[cut_columns_indexes].tolist())

        violation_count = a[cut_columns_indexes][0]

        if violation_count == 0:
            cut2.append("v1") #"v1=0"
        elif violation_count <= 5:
            cut2.append("v2") #"v2<=2"
        elif violation_count <= 10:
            cut2.append("v3") #"v3<=5"
        else:
            cut2.append("v4") #"v4>5"

    return cut1, cut2, feature_names


if __name__ == "__main__":
    # iris_demo()

    result_sets = communication.get_training_dataset(
        experiment_id=communication.get_current_experiment()["id"],
        training_dataset_size=1000
    )

    is_backend_id = True
    backend_id = 0

    for result_set in result_sets:

        if is_backend_id:
            is_backend_id = False
            backend_id = result_set[1][0]
        else:
            is_backend_id = True

            # "clock",
            # "sampled_read_violation_count",
            # "sampled_write_violation_count",
            # "sampled_available_write_iops_mean",
            # "sampled_available_read_iops_mean",
            # "live_volume_count_during_clock",
            # "requested_write_iops_total",
            # "requested_read_iops_total",

            x, y, feature_names = prepare_traning_dataset(
                result_set,
                target_column="sampled_write_violation_count",
                ignore_columns=[
                    "sampled_read_violation_count"
                    #, "requested_read_iops_total"
                    #, "requested_write_iops_total"
                ]
            )

            # from sklearn.svm import SVC
            # clf = SVC()
            # clf.fit(x, y)

            # from sklearn.naive_bayes import GaussianNB
            # clf = GaussianNB()
            # clf = clf.fit(x, y)

            from sklearn import tree
            clf = tree.ExtraTreeClassifier()
            clf = clf.fit(x, y)

            # from sklearn import linear_model
            #
            # clf = linear_model.BayesianRidge()
            # clf.fit(x, y)

            # from sklearn.neural_network import MLPClassifier
            #
            # clf = MLPClassifier(solver='lbfgs', alpha=1e-5,
            #     hidden_layer_sizes = (5, 2), random_state = 1)
            # clf.fit(x, y)


            from sklearn.model_selection import cross_val_score
            scores = cross_val_score(clf, x, y, cv=10)
            print("mean: {:.3f} (std: {:.3f})".format(scores.mean(),
                                                      scores.std()))

            import pydotplus
            dot_data = tree.export_graphviz(
                clf, out_file=None,
                feature_names=feature_names,
                class_names=clf.classes_,
                filled=True, rounded=True,
                special_characters=True)
            graph = pydotplus.graph_from_dot_data(dot_data)
            png = graph.create_png()
            fh = open("backend_%s.png" % str(backend_id), "wb")
            fh.write(png)
            fh.close()

    # clf = tree.DecisionTreeClassifier()
    # clf = clf.fit(x, y)

    # print result_sets[1][0]['requested_write_ios_total']

    # a = 12;
    pass
