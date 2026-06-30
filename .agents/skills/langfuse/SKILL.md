---
name: langfuse
description: Provides specialized context, rules, and tools for implementing, configuring, and debugging langfuse. Use this skill whenever modifying langfuse-docs configurations or adding related functionality.
---
# langfuse-docs

## File Tree

```text
langfuse/
├── assets
├── modules
│   ├── langfuse (See AST Map below)
│   ├── langfuse-docs
│   └── langfuse-python (See AST Map below)
├── references
├── scripts
└── SKILL.md
```

> **Agent Instructions:** The AST maps below provide a high-level overview of the `modules/` directory. Note that the complete repository source code is available within the `modules/` folder. You can and should use your file reading tools to access the actual source code within `modules/` for complete details, implementation logic, and context beyond what the AST map provides.

### AST Map: `modules/langfuse`

```python
packages\shared\src\domain\observation-field-groups.ts:
⋮
│export type ObservationFieldGroupFull =
⋮

packages\shared\src\domain\scores.ts:
⋮
│export type ScoreDataTypeType = z.infer<typeof ScoreDataTypeDomain>;
│
⋮

packages\shared\src\errors\BaseError.ts:
│export class BaseError extends Error {
⋮
│  public isUserError(): boolean {
│    return this.httpCode >= 400 && this.httpCode < 500;
⋮

packages\shared\src\features\entitlements\plans.ts:
⋮
│export type Plan = keyof typeof planLabels;
│
⋮

packages\shared\src\features\monitors\scheduler\scheduler.ts:
⋮
│type FilterState = z.infer<typeof singleFilter>[];
│
⋮

packages\shared\src\features\monitors\scheduler\types.ts:
⋮
│export type MonitorWebhookQueueEvent = z.infer<
│  typeof MonitorWebhookQueueEventSchema
⋮

packages\shared\src\tableDefinitions\types.ts:
│export type UiColumnMatchable = Readonly<{
⋮

packages\shared\src\types.ts:
⋮
│export type FilterState = FilterCondition[];
⋮

packages\shared\src\utils\chatml\types.ts:
│export type NormalizerContext = {
⋮

web\src\components\session\TraceEventsRow.tsx:
⋮
│                    <NewDatasetItemFromTraceId
│                      projectId={projectId}
│                      traceId={trace.id}
│                      timestamp={new Date(trace.timestamp)}
⋮

web\src\components\session\TraceRow.tsx:
⋮
│type LazyTraceRowProps = {
│  trace: RouterOutputs["sessions"]["byIdWithScores"]["traces"][number];
│  projectId: string;
│  openPeek: (id: string, row: any) => void;
│  index: number;
│  traceCommentCounts: Map<string, number> | undefined;
⋮
│                <NewDatasetItemFromTraceId
│                  projectId={projectId}
│                  traceId={trace.id}
│                  timestamp={new Date(trace.timestamp)}
⋮

web\src\components\table\data-table-controls.clienttest.tsx:
⋮
│        <CategoricalFacet
│          label="Type"
│          filterKey="type"
│          expanded
│          loading={false}
│          options={[]}
│          counts={new Map()}
│          value={["AGENT"]}
│          onChange={() => {}}
│          isActive
│          isDisabled={false}
⋮

web\src\features\batch-exports\components\BatchExportsTable.tsx:
⋮
│        return (
│          <div className="flex items-center gap-2">
│            <span className="whitespace-break-spaces">{name}</span>
│            <TooltipProvider>
│              <Tooltip>
│                <TooltipTrigger>
│                  <InfoIcon className="text-muted-foreground size-3" />
│                </TooltipTrigger>
│                <TooltipContent>
│                  <div className="space-y-1">
│                    <div>Created: {new Date(createdAt).toLocaleString()}</div>
⋮

web\src\features\experiments\components\table\ExperimentsTable.tsx:
⋮
│                pagination={{
│                  totalCount,
│                  onChange: (updater) => {
│                    const newState =
│                      typeof updater === "function"
⋮
│                    setPaginationState({
│                      page: newState.pageIndex + 1,
│                      limit: newState.pageSize,
⋮

web\src\pages\project\[projectId]\settings\integrations\blobstorage.tsx:
⋮
│                  <>
│                    <br />
│                    <span className="text-xs opacity-70">
│                      {new Date(state.data.config.lastErrorAt).toLocaleString()}
⋮

worker\src\__tests__\periodicRunner.test.ts:
⋮
│class TestRunner extends PeriodicRunner {
│  public callCount = 0;
│  public shouldThrow = false;
│  public returnInterval: number | undefined = undefined;
│
│  protected get name(): string {
│    return "test-runner";
│  }
│
│  protected get defaultIntervalMs(): number {
⋮

worker\src\utils\RedisLock.ts:
⋮
│export type OnUnavailableBehavior = "proceed" | "fail";
│
⋮
```

### AST Map: `modules/langfuse-python`

```python
langfuse\_client\attributes.py:
⋮
│def _flatten_and_serialize_metadata_values(
│    metadata: Optional[Dict[str, Any]],
│) -> Optional[Dict[str, str]]:
│    if metadata is None:
⋮
│    def flatten_value(path: str, value: Any) -> None:
⋮

langfuse\_client\constants.py:
⋮
│def get_observation_types_list(
│    literal_type: Any,
⋮

langfuse\_task_manager\media_upload_queue.py:
⋮
│class UploadMediaJob(TypedDict):
⋮

langfuse\_utils\serializer.py:
⋮
│def serialize_datetime(v: dt.datetime) -> str:
│    def _serialize_zoned_datetime(v: dt.datetime) -> str:
│        if v.tzinfo is not None and v.tzinfo.tzname(None) == dt.timezone.utc.tzname(
│            None
│        ):
│            # UTC is a special case where we use "Z" at the end instead of "+00:00"
│            return v.isoformat().replace("+00:00", "Z")
│        else:
│            # Delegate to the typical +/- offset format
⋮

langfuse\api\commons\errors\access_denied_error.py:
⋮
│class AccessDeniedError(ApiError):
⋮

langfuse\api\core\api_error.py:
⋮
│class ApiError(Exception):
⋮

langfuse\api\core\datetime_utils.py:
⋮
│def serialize_datetime(v: dt.datetime) -> str:
│    """
│    Serialize a datetime including timezone info.
│
│    Uses the timezone info provided if present, otherwise uses the current runtime's timezone info.
│
│    UTC datetimes end in "Z" while all other timezones are represented as offset from UTC, e.g. +05
⋮
│    def _serialize_zoned_datetime(v: dt.datetime) -> str:
⋮

langfuse\api\core\jsonable_encoder.py:
⋮
│def jsonable_encoder(
│    obj: Any, custom_encoder: Optional[Dict[Any, Callable[[Any], Any]]] = None
⋮

langfuse\api\core\pydantic_utilities.py:
⋮
│def parse_obj_as(type_: Type[T], object_: Any) -> T:
⋮

langfuse\api\core\serialization.py:
⋮
│class FieldMetadata:
⋮
│def convert_and_respect_annotation_metadata(
│    *,
│    object_: typing.Any,
│    annotation: typing.Any,
│    inner_type: typing.Optional[typing.Any] = None,
│    direction: typing.Literal["read", "write"],
⋮
│def _convert_mapping(
│    object_: typing.Mapping[str, object],
│    expected_type: typing.Any,
│    direction: typing.Literal["read", "write"],
⋮
│def _get_annotation(type_: typing.Any) -> typing.Optional[typing.Any]:
⋮
│def _remove_annotations(type_: typing.Any) -> typing.Any:
⋮
│def _get_alias_to_field_name(
│    field_to_hint: typing.Dict[str, typing.Any],
⋮
│def _get_field_to_alias_name(
│    field_to_hint: typing.Dict[str, typing.Any],
⋮
│def _get_alias_from_type(type_: typing.Any) -> typing.Optional[str]:
⋮
│def _alias_key(
│    key: str,
│    type_: typing.Any,
│    direction: typing.Literal["read", "write"],
│    aliases_to_field_names: typing.Dict[str, str],
⋮

langfuse\api\unstable\errors\errors\method_not_allowed_error.py:
⋮
│class MethodNotAllowedError(ApiError):
⋮

langfuse\api\unstable\errors\errors\not_found_error.py:
⋮
│class NotFoundError(ApiError):
⋮

langfuse\api\unstable\errors\errors\unauthorized_error.py:
⋮
│class UnauthorizedError(ApiError):
⋮

tests\unit\test_openai_prompt_extraction.py:
⋮
│def test_openai_value_serialization_fallback_stays_json_safe():
│    class UnknownLeaf:
│        def __str__(self):
⋮
│    class FallbackModel(BaseModel):
│        created_at: datetime
⋮
│        def model_dump(self, *args, **kwargs):
⋮
```