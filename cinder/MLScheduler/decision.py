import communication
import pdb
from sklearn import tree
# from tableausdk import *

# from sklearn.datasets import load_iris
# from sklearn import tree
# iris = load_iris()
# clf = tree.DecisionTreeClassifier()
# clf = clf.fit(iris.data, iris.target)
#
# with open("iris.dot", 'w') as f:
#     f = tree.export_graphviz(clf, out_file=f)
from IPython.display import Image


def cut_dataset(result_set, columns):

    # for column in

    pass


if __name__ == "__main__":
    result_sets = communication.get_training_dataset(
        experiment_id=communication.get_current_experiment()["id"],
        training_dataset_size=10
    )

    is_backend_id = True

    for result_set in result_sets:

        if is_backend_id:
            is_backend_id = False
        else:
            is_backend_id = True

            cut_dataset(
                result_set,
                (
                    "sampled_read_violation_count",
                    # "clock",
                    # "sampled_read_violation_count",
                    # "sampled_write_violation_count",
                    # "sampled_available_write_iops_mean",
                    # "sampled_available_read_iops_mean",
                    # "live_volume_count_during_clock",
                    # "requested_write_iops_total",
                    # "requested_read_iops_total",
                ))

    print result_sets[1][0]['requested_write_ios_total']

    a = 12;
    pass
