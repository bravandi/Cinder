import tools
import communication
import numpy as np
import pdb
from datetime import datetime
from classification_with_python import ClassificationWithPython


class MachineLearningAlgorithm:
    @staticmethod
    def RepTree():
        return "reptree"

    @staticmethod
    def Regression():
        return "regression"

    @staticmethod
    def J48():
        return "j48"

    @staticmethod
    def BayesianNetwork():
        return "bayesiannetwork"


class Classification:
    current_classification = None

    def __init__(self,
                 classifier_name, violation_iops_classes,
                 read_is_priority, training_experiment_id, use_java_service,
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
        self.use_java_service = use_java_service
        self.python_classification = None

        if self.use_java_service is True:
            self.python_classification = ClassificationWithPython()

    @staticmethod
    def get_current_or_initialize(
            training_dataset_size,
            violation_iops_classes,
            training_experiment_id,
            read_is_priority):

        if Classification.current_classification is None:
            clf = Classification(
                classifier_name="tree",
                violation_iops_classes=violation_iops_classes,
                read_is_priority=read_is_priority,
                training_experiment_id=training_experiment_id,
                use_java_service=True  # TODO hard coded
            )

            if clf.use_java_service is False:
                # use python for machine learning
                clf.python_classification.create_models(
                    training_dataset_size=training_dataset_size
                )

            Classification.current_classification = clf

        return Classification.current_classification

    def predict(self, volume_request_id):

        if communication.Communication.get_config("is_training") is True:
            return None

        clock = communication.get_volume_performance_meter_clock_calc(datetime.now())

        if self.use_java_service is False:

            return self.python_classification.predict_with_python_machine_learning_implimentation(
                clock, volume_request_id)

        else:

            return self._predict_with_java_service(clock, volume_request_id)

    def _predict_with_java_service(self, clock, volume_request_id):

        try:

            predictions_list = communication.get_prediction_from_java_service(
                volume_request_id=volume_request_id,
                clock=clock,
                algorithm=MachineLearningAlgorithm.J48(),
                training_experiment_id=communication.Communication.get_training_experiment_id()
            )

            tools.log(
                type="INFO",
                code="java_service_cant_connect",
                file_name="classification.py",
                function_name="predictions",
                message="predictions: %s" + str(predictions_list)
            )

        except Exception as err:

            tools.log(
                type="ERROR",
                code="java_service_cant_connect",
                file_name="classification.py",
                function_name="_predict_with_java_service",
                message="cannot connect to the java service",
                exception=err
            )

            return None

        read_candidates = []
        write_candidates = []
        assessment_policy = communication.Communication.get_assessment_policy()

        for backend_prediction in predictions_list:
            self.pick_for_read(
                cinder_id=backend_prediction["cinder_id"],
                prediction_probabilities=backend_prediction["read_predictions"],
                candidate_list=read_candidates,
                assessment_policy=assessment_policy,
                number_of_volumes_plus_requested=backend_prediction["number_of_volumes_plus_requested"])

            self.pick_for_write(
                cinder_id=backend_prediction["cinder_id"],
                prediction_probabilities=backend_prediction["write_predictions"],
                candidate_list=write_candidates,
                assessment_policy=assessment_policy,
                number_of_volumes_plus_requested=backend_prediction["number_of_volumes_plus_requested"])

        final_result = np.intersect1d(read_candidates, write_candidates).tolist()

        if len(final_result) == 0:
            if self.read_is_priority:
                final_result = read_candidates
            else:
                final_result = write_candidates

        # if len(final_result) == 0:
        #     pdb.set_trace()

        return final_result

    def _assessment_policy_do_compare(
            self,
            prediction_probabilities,
            comparison_string,
            number_of_volumes_plus_requested
    ):
        result = None

        for violation_iops_class in self.violation_iops_classes.keys():
            comparison_string = comparison_string.replace(
                "[" + violation_iops_class + "]",
                "prediction_probabilities[%s]" % str(self.violation_iops_classes[violation_iops_class]));

        comparison_string = "result = " + comparison_string.replace("vol_count", "number_of_volumes_plus_requested")

        exec (comparison_string)

        return result

    def pick_for_read(self,
                      cinder_id, prediction_probabilities, candidate_list, assessment_policy,
                      number_of_volumes_plus_requested):

        # if prediction_probabilities[self.violation_iops_classes["v1"]] >= 0.5:
        #     candidate_list.append(cinder_id)

        if assessment_policy == communication.AssessmentPolicy.max_efficiency():
            # compareTo = new double[] { 0.6, 0.6, 0.6 };
            # if (predictors[0] > compareTo[0] || predictors[1] > compareTo[1]
            # //|| predictors[2] > compareTo[2]) {

            if self._assessment_policy_do_compare(
                    prediction_probabilities=prediction_probabilities,
                    comparison_string="vol_count == 1 or [v1] > 0.6 or [v2] > 0.6 or [v3] > 0.6 or [v4] > 0",
                    number_of_volumes_plus_requested=number_of_volumes_plus_requested):
                candidate_list.append(cinder_id)

        if assessment_policy == communication.AssessmentPolicy.efficiency_first():
            # compareTo = new double[] { 0.8, 0.95, 0.98 };
            # if (volNum == 0 || predictors[0] > compareTo[0]
            # // || predictors[1] > compareTo[1] || predictors[2] > compareTo[2]

            if self._assessment_policy_do_compare(
                    prediction_probabilities=prediction_probabilities,
                    comparison_string="vol_count == 1 or [v1] > 0.8 or [v2] > 0.95 or [v3] > 0.95 or [v4] > 0",
                    number_of_volumes_plus_requested=number_of_volumes_plus_requested):
                candidate_list.append(cinder_id)

        if assessment_policy == communication.AssessmentPolicy.qos_first():
            # compareTo = new double[] { 0.90, 0.49 };
            # if (volNum == 0 || predictors[0] > compareTo[0]
            # //|| predictors[1] > compareTo[1]

            if self._assessment_policy_do_compare(
                    prediction_probabilities=prediction_probabilities,
                    comparison_string="vol_count == 1 or [v1] > 0.8 or [v2] > 0.95 or [v3] > 0.95 or [v4] > 0",
                    number_of_volumes_plus_requested=number_of_volumes_plus_requested):
                candidate_list.append(cinder_id)

        if assessment_policy == communication.AssessmentPolicy.strict_qos():
            # if (volNum == 0 || predictors[0] > compareTo[0]) {
            # if (volNum == 0 || (predictors[0] > compareTo[0] && (predictors[0] + predictors[1] > compareTo[1]))) {

            if self._assessment_policy_do_compare(
                    prediction_probabilities=prediction_probabilities,
                    comparison_string="vol_count == 1 or [v1] > 0.8 or [v2] > 0.95 or [v3] > 0.95 or [v4] > 0",
                    number_of_volumes_plus_requested=number_of_volumes_plus_requested):
                candidate_list.append(cinder_id)

    def pick_for_write(self, cinder_id, prediction_probabilities, candidate_list, assessment_policy,
                       number_of_volumes_plus_requested):

        if assessment_policy == communication.AssessmentPolicy.max_efficiency():
            if self._assessment_policy_do_compare(
                    prediction_probabilities=prediction_probabilities,
                    comparison_string="vol_count > 0 or [v1] > 0.6 or [v2] > 0.6 or [v3] > 0.6 or [v4] > 0",
                    number_of_volumes_plus_requested=number_of_volumes_plus_requested):
                candidate_list.append(cinder_id)

        if assessment_policy == communication.AssessmentPolicy.efficiency_first():
            if self._assessment_policy_do_compare(
                    prediction_probabilities=prediction_probabilities,
                    comparison_string="vol_count == 1 or [v1] > 0.8 or [v2] > 0.95 or [v3] > 0.95 or [v4] > 0",
                    number_of_volumes_plus_requested=number_of_volumes_plus_requested):
                candidate_list.append(cinder_id)

        if assessment_policy == communication.AssessmentPolicy.qos_first():
            if self._assessment_policy_do_compare(
                    prediction_probabilities=prediction_probabilities,
                    comparison_string="vol_count == 1 or [v1] > 0.8 or [v2] > 0.95 or [v3] > 0.95 or [v4] > 0",
                    number_of_volumes_plus_requested=number_of_volumes_plus_requested):
                candidate_list.append(cinder_id)

        if assessment_policy == communication.AssessmentPolicy.strict_qos():
            if self._assessment_policy_do_compare(
                    prediction_probabilities=prediction_probabilities,
                    comparison_string="vol_count == 1 or [v1] > 0.8 or [v2] > 0.95 or [v3] > 0.95 or [v4] > 0",
                    number_of_volumes_plus_requested=number_of_volumes_plus_requested):
                candidate_list.append(cinder_id)


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
