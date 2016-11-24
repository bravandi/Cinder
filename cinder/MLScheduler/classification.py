import tools
import communication
import numpy as np
import pdb
from datetime import datetime
from sklearn import tree
from sklearn.model_selection import cross_val_score


class Classification:
    current_classification = None

    def __init__(self,
                 classifier_name, violation_iops_classes,
                 read_is_priority, training_experiment_id,
                 draw_decision_tree=False, run_cross_validation=False):

        self.training_experiment_id = training_experiment_id
        self.read_is_priority = read_is_priority
        self.violation_iops_classes = violation_iops_classes
        self.classifier_name = classifier_name
        self.draw_decision_tree = draw_decision_tree
        self.run_cross_validation = run_cross_validation
        self.classifiers_for_read_iops = {}
        self.classifiers_for_write_iops = {}
        self.create_time = datetime.now()

    @staticmethod
    def get_current_or_initialize(training_dataset_size, violation_iops_classes, training_experiment_id):

        if Classification.current_classification is None:
            clf = Classification(
                classifier_name="tree",
                violation_iops_classes=violation_iops_classes,
                read_is_priority=True,
                training_experiment_id=training_experiment_id
            )

            clf.create_models(
                training_dataset_size=training_dataset_size
            )

            Classification.current_classification = clf

        return Classification.current_classification

    def prepare_traning_dataset(self, result_set, target_column, ignore_columns=[]):
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
                cut2.append("v1")  # "v1=0"
            elif violation_count <= 3:
                cut2.append("v2")  # "v2<=2"
            elif violation_count <= 5:
                cut2.append("v3")  # "v3<=5"
            else:
                cut2.append("v4")  # "v4>5"

        return cut1, cut2, feature_names

    def create_models(self, training_dataset_size):
        if communication.Communication.get_config("is_training") is True:
            return None

        training_data = communication.get_training_dataset(
            experiment_id=self.training_experiment_id,
            training_dataset_size=training_dataset_size
        )

        self.create_model(training_data, for_read_iops=True)
        self.create_model(training_data, for_read_iops=False)

    def create_model(self, training_data, for_read_iops):

        is_backend_id = True
        backend_id = 0
        cinder_id = ''

        # "clock",
        # "sampled_read_violation_count",
        # "sampled_write_violation_count",
        # "live_volume_count_during_clock",
        # "requested_write_iops_total",
        # "requested_read_iops_total",
        if for_read_iops:
            target_column = "sampled_read_violation_count"
            ignore_columns = ["sampled_write_violation_count"]
        else:
            target_column = "sampled_write_violation_count"
            ignore_columns = ["sampled_read_violation_count"]

        for result_set in training_data:

            if is_backend_id:
                is_backend_id = False
                backend_id = result_set[1][0]
                cinder_id = result_set[1][1]
            else:
                is_backend_id = True

                x, y, feature_names = self.prepare_traning_dataset(
                    result_set,
                    target_column=target_column,
                    ignore_columns=ignore_columns
                )

                # from sklearn.svm import SVC
                # clf = SVC()
                # clf.fit(x, y)

                # from sklearn.naive_bayes import GaussianNB
                # clf = GaussianNB()
                # clf = clf.fit(x, y)

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

                if for_read_iops:
                    self.classifiers_for_read_iops[cinder_id] = {
                        "classifier": clf,
                        "backend_id": backend_id
                    }
                else:
                    self.classifiers_for_write_iops[cinder_id] = {
                        "classifier": clf,
                        "backend_id": backend_id
                    }

                if self.run_cross_validation:
                    try:
                        scores = cross_val_score(clf, x, y, cv=10)
                        print("mean: {:.3f} (std: {:.3f})".format(scores.mean(),
                                                                  scores.std()))
                    except Exception as err:
                        tools.log("ERROR on cross validation for %s for for_read_iops=%s. MSG: %s " %
                                  (cinder_id, str(for_read_iops), str(err)))

                if self.draw_decision_tree and isinstance(clf, tree.DecisionTreeClassifier):
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

    def _include_classes_with_zero_probability(self, classifier, prediction):

        classes = {}

        for cls in self.violation_iops_classes:
            classes[cls] = 0.0

        classes_from_clf = list(classifier.classes_)

        for cls in classes.keys():
            if cls in classes_from_clf:
                classes[cls] = round(prediction[classes_from_clf.index(cls)], 5)

        return classes

    def predict(self, volume_request_id):

        classifier_predictions = {}
        values = {}

        if communication.Communication.get_config("is_training") is True:
            return None

        weights = communication.get_backends_weights(
            experiment_id=communication.Communication.get_current_experiment()["id"],
            volume_request_id=volume_request_id)

        # there were no records for training or prediction. Probably its a trainng experiment
        if len(weights) == 1 or len(self.classifiers_for_read_iops) == 0 or len(self.classifiers_for_write_iops) == 0:
            return None

        volume_request = weights[0][0]
        clock = communication.get_volume_performance_meter_clock_calc(datetime.now())

        for backend_weight in weights[1:]:
            row = backend_weight[0]

            values[row["cinder_id"]] = [[
                clock,
                row["live_volume_count_during_clock"] + 1,
                row["requested_write_iops_total"] + volume_request["write_iops"],
                row["requested_read_iops_total"] + volume_request["read_iops"]
            ]]

        for cinder_id in self.classifiers_for_read_iops.keys():

            if cinder_id not in values:
                continue

            read_classifier = self.classifiers_for_read_iops[cinder_id]["classifier"]
            write_classifier = self.classifiers_for_write_iops[cinder_id]["classifier"]

            values_array = values[cinder_id]

            classifier_predictions[cinder_id] = {
                "read_violation": {
                    # "class": read_classifier.predict(values_array)[0],
                    "prob": self._include_classes_with_zero_probability(
                        read_classifier,
                        list(read_classifier.predict_proba(values_array)[0]))
                },
                "write_violation": {
                    # "class": write_classifier.predict(values_array)[0],
                    "prob": self._include_classes_with_zero_probability(
                        write_classifier,
                        list(write_classifier.predict_proba(values_array)[0]))
                }
            }

        read_candidates = {}
        write_candidates = {}

        # calculate predictions
        for cinder_id, predictions in classifier_predictions.iteritems():

            for read_or_write_iops, prediction in predictions.iteritems():
                prob = np.array(prediction["prob"].values())

                if read_or_write_iops == "read_violation":
                    w = np.array([4, 3, 2, 1])

                if read_or_write_iops == "write_violation":
                    w = np.array([4, 3, 2, 1])

                val = prob * w
                best_index = val.argmax()
                prediction["recommendation"] = {self.violation_iops_classes[val.argmax()]: prob[best_index]}

                if read_or_write_iops == "read_violation":
                    read_candidates[cinder_id] = prediction["recommendation"]

                if read_or_write_iops == "write_violation":
                    write_candidates[cinder_id] = prediction["recommendation"]

        max_value_read = max([value.values()[0] for key, value in read_candidates.iteritems()])
        read_final_candidates = [key for key, value in read_candidates.iteritems()
                                 if value.values()[0] == max_value_read]

        max_value_write = max([value.values()[0] for key, value in write_candidates.iteritems()])
        write_final_candidates = [key for key, value in write_candidates.iteritems()
                                  if value.values()[0] == max_value_write]

        final_result = np.intersect1d(read_final_candidates, write_final_candidates).tolist()

        if len(final_result) == 0:
            if self.read_is_priority:
                final_result = read_final_candidates
            else:
                final_result = write_final_candidates

        return final_result


if __name__ == "__main__":
    # d = Classification(
    #     classifier_name="tree",
    #     violation_iops_classes=["v1", "v2", "v3", "v4"],
    #     read_is_priority=True,
    #     training_experiment_id=0
    # )
    #
    # d.create_models(
    #     training_dataset_size=300
    # )
    #
    # print d.predict(
    #     volume_request_id=2352
    # )
    pass