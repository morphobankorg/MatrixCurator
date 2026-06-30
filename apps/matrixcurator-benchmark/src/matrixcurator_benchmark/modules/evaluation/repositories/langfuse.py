import os
from typing import Any

from langfuse import Langfuse
from langfuse.api.commons import ConfigCategory, ScoreConfigDataType
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langfuse.api.unstable.commons import (
    EvaluationRuleMapping,
    EvaluationRuleMappingSource,
    EvaluationRuleTarget,
    EvaluatorModelConfig,
    EvaluatorOutputDataType,
    EvaluatorOutputDefinition_Categorical,
    EvaluatorOutputFieldDefinition,
    EvaluatorScope,
)
from langfuse.api.unstable.evaluation_rules import (
    CreateLlmAsJudgeEvaluationRuleRequest,
    LlmAsJudgeEvaluationRuleEvaluatorReference,
)
from langfuse.api.unstable.evaluators import CreateEvaluatorRequest_LlmAsJudge

from lume import structlog


logger = structlog.get_logger(__name__)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def create_score_config(
    client: Langfuse, name: str, categories: list[dict[str, Any]], description: str
) -> str:
    """Creates a score config in Langfuse if it doesn't exist, returning its ID."""
    score_config_id = None
    try:
        score_configs = client.api.score_configs.get()
        for sc in score_configs.data:
            if sc.name == name:
                score_config_id = sc.id
                break
    except Exception as e:
        logger.warning("Failed to fetch score configs", error=str(e))

    if not score_config_id:
        logger.info("Creating score config", config_name=name)
        new_config = client.api.score_configs.create(
            name=name,
            data_type=ScoreConfigDataType.CATEGORICAL,
            categories=[ConfigCategory(**cat) for cat in categories],
            description=description,
        )
        score_config_id = new_config.id
    else:
        logger.info(
            "Score config already exists", config_name=name, config_id=score_config_id
        )

    return score_config_id


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def create_evaluator(
    client: Langfuse,
    evaluator_name: str,
    prompt_text: str,
    score_config_id: str,
    categories: list[str],
) -> str:
    """Creates an evaluator in Langfuse."""
    eval_provider = os.getenv("LANGFUSE_EVAL_PROVIDER", "google")
    eval_model = os.getenv("LANGFUSE_EVAL_MODEL", "gemini-3.5-flash")

    evaluator = client.api.unstable.evaluators.create(
        request=CreateEvaluatorRequest_LlmAsJudge(
            name=evaluator_name,
            prompt=prompt_text,
            output_definition=EvaluatorOutputDefinition_Categorical(
                data_type=EvaluatorOutputDataType.CATEGORICAL,
                reasoning=EvaluatorOutputFieldDefinition(
                    description="Explain why this category was assigned based on the semantic match."
                ),
                score={
                    "configId": score_config_id,
                    "description": "Select the best category label from the defined score config.",
                    "categories": categories,
                    "should_allow_multiple_matches": False,
                },
            ),
            model_config_=EvaluatorModelConfig(
                provider=eval_provider, model=eval_model
            ),
        )
    )
    logger.info("Evaluator created or updated", evaluator_id=evaluator.id)
    return evaluator.id


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def bind_evaluation_rule(
    client: Langfuse, rule_name: str, evaluator_name: str, dataset_name: str
) -> None:
    """Binds an evaluation rule to a specific dataset."""
    try:
        existing_rules = client.api.unstable.evaluation_rules.list().data
        existing_rule_names = [rule.name for rule in existing_rules]

        if rule_name not in existing_rule_names:
            logger.info("Creating Evaluation Rule", rule_name=rule_name)
            client.api.unstable.evaluation_rules.create(
                request=CreateLlmAsJudgeEvaluationRuleRequest(
                    name=rule_name,
                    evaluator=LlmAsJudgeEvaluationRuleEvaluatorReference(
                        name=evaluator_name, scope=EvaluatorScope.PROJECT
                    ),
                    target=EvaluationRuleTarget.EXPERIMENT,
                    enabled=True,
                    sampling=1.0,
                    filter=[
                        {
                            "type": "stringOptions",
                            "column": "datasetName",
                            "operator": "any of",
                            "value": [dataset_name],
                        }
                    ],
                    mapping=[
                        EvaluationRuleMapping(
                            variable="output", source=EvaluationRuleMappingSource.OUTPUT
                        ),
                        EvaluationRuleMapping(
                            variable="expected_output",
                            source=EvaluationRuleMappingSource.EXPECTED_OUTPUT,
                        ),
                    ],
                )
            )
        else:
            logger.info("Evaluation Rule already exists", rule_name=rule_name)
    except Exception as e:
        error_str = str(e)
        logger.warning(
            "Failed to setup Managed Evaluator or Rules via API", error=error_str
        )
        if "422" in error_str and "No valid LLM model found" in error_str:
            logger.warning(
                "ACTION REQUIRED: Langfuse Cloud rejected the Evaluator Model configuration. "
                "You must log into your Langfuse project dashboard, go to Settings > Model Providers, "
                "and configure the API credentials for your chosen provider. "
                "Ensure that the provider and model match the values set in LANGFUSE_EVAL_PROVIDER "
                "and LANGFUSE_EVAL_MODEL."
            )
