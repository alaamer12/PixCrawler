## pydantic_settings

```python
class BaseSettings(BaseModel):
    """
    Base class for settings, allowing values to be overridden by environment variables.

    This is useful in production for secrets you do not wish to save in code, it plays nicely with docker(-compose),
    Heroku and any 12 factor app design.

    All the below attributes can be set via `model_config`.

    Args:
        _case_sensitive: Whether environment and CLI variable names should be read with case-sensitivity.
            Defaults to `None`.
        _nested_model_default_partial_update: Whether to allow partial updates on nested model default object fields.
            Defaults to `False`.
        _env_prefix: Prefix for all environment variables. Defaults to `None`.
        _env_file: The env file(s) to load settings values from. Defaults to `Path('')`, which
            means that the value from `model_config['env_file']` should be used. You can also pass
            `None` to indicate that environment variables should not be loaded from an env file.
        _env_file_encoding: The env file encoding, e.g. `'latin-1'`. Defaults to `None`.
        _env_ignore_empty: Ignore environment variables where the value is an empty string. Default to `False`.
        _env_nested_delimiter: The nested env values delimiter. Defaults to `None`.
        _env_nested_max_split: The nested env values maximum nesting. Defaults to `None`, which means no limit.
        _env_parse_none_str: The env string value that should be parsed (e.g. "null", "void", "None", etc.)
            into `None` type(None). Defaults to `None` type(None), which means no parsing should occur.
        _env_parse_enums: Parse enum field names to values. Defaults to `None.`, which means no parsing should occur.
        _cli_prog_name: The CLI program name to display in help text. Defaults to `None` if _cli_parse_args is `None`.
            Otherwise, defaults to sys.argv[0].
        _cli_parse_args: The list of CLI arguments to parse. Defaults to None.
            If set to `True`, defaults to sys.argv[1:].
        _cli_settings_source: Override the default CLI settings source with a user defined instance. Defaults to None.
        _cli_parse_none_str: The CLI string value that should be parsed (e.g. "null", "void", "None", etc.) into
            `None` type(None). Defaults to _env_parse_none_str value if set. Otherwise, defaults to "null" if
            _cli_avoid_json is `False`, and "None" if _cli_avoid_json is `True`.
        _cli_hide_none_type: Hide `None` values in CLI help text. Defaults to `False`.
        _cli_avoid_json: Avoid complex JSON objects in CLI help text. Defaults to `False`.
        _cli_enforce_required: Enforce required fields at the CLI. Defaults to `False`.
        _cli_use_class_docs_for_groups: Use class docstrings in CLI group help text instead of field descriptions.
            Defaults to `False`.
        _cli_exit_on_error: Determines whether or not the internal parser exits with error info when an error occurs.
            Defaults to `True`.
        _cli_prefix: The root parser command line arguments prefix. Defaults to "".
        _cli_flag_prefix_char: The flag prefix character to use for CLI optional arguments. Defaults to '-'.
        _cli_implicit_flags: Whether `bool` fields should be implicitly converted into CLI boolean flags.
            (e.g. --flag, --no-flag). Defaults to `False`.
        _cli_ignore_unknown_args: Whether to ignore unknown CLI args and parse only known ones. Defaults to `False`.
        _cli_kebab_case: CLI args use kebab case. Defaults to `False`.
        _cli_shortcuts: Mapping of target field name to alias names. Defaults to `None`.
        _secrets_dir: The secret files directory or a sequence of directories. Defaults to `None`.
    """

    def __init__(
        __pydantic_self__,
        _case_sensitive: bool | None = None,
        _nested_model_default_partial_update: bool | None = None,
        _env_prefix: str | None = None,
        _env_file: DotenvType | None = ENV_FILE_SENTINEL,
        _env_file_encoding: str | None = None,
        _env_ignore_empty: bool | None = None,
        _env_nested_delimiter: str | None = None,
        _env_nested_max_split: int | None = None,
        _env_parse_none_str: str | None = None,
        _env_parse_enums: bool | None = None,
        _cli_prog_name: str | None = None,
        _cli_parse_args: bool | list[str] | tuple[str, ...] | None = None,
        _cli_settings_source: CliSettingsSource[Any] | None = None,
        _cli_parse_none_str: str | None = None,
        _cli_hide_none_type: bool | None = None,
        _cli_avoid_json: bool | None = None,
        _cli_enforce_required: bool | None = None,
        _cli_use_class_docs_for_groups: bool | None = None,
        _cli_exit_on_error: bool | None = None,
        _cli_prefix: str | None = None,
        _cli_flag_prefix_char: str | None = None,
        _cli_implicit_flags: bool | None = None,
        _cli_ignore_unknown_args: bool | None = None,
        _cli_kebab_case: bool | None = None,
        _cli_shortcuts: Mapping[str, str | list[str]] | None = None,
        _secrets_dir: PathType | None = None,
        **values: Any,
    ) -> None:
        super().__init__(
            **__pydantic_self__._settings_build_values(
                values,
                _case_sensitive=_case_sensitive,
                _nested_model_default_partial_update=_nested_model_default_partial_update,
                _env_prefix=_env_prefix,
                _env_file=_env_file,
                _env_file_encoding=_env_file_encoding,
                _env_ignore_empty=_env_ignore_empty,
                _env_nested_delimiter=_env_nested_delimiter,
                _env_nested_max_split=_env_nested_max_split,
                _env_parse_none_str=_env_parse_none_str,
                _env_parse_enums=_env_parse_enums,
                _cli_prog_name=_cli_prog_name,
                _cli_parse_args=_cli_parse_args,
                _cli_settings_source=_cli_settings_source,
                _cli_parse_none_str=_cli_parse_none_str,
                _cli_hide_none_type=_cli_hide_none_type,
                _cli_avoid_json=_cli_avoid_json,
                _cli_enforce_required=_cli_enforce_required,
                _cli_use_class_docs_for_groups=_cli_use_class_docs_for_groups,
                _cli_exit_on_error=_cli_exit_on_error,
                _cli_prefix=_cli_prefix,
                _cli_flag_prefix_char=_cli_flag_prefix_char,
                _cli_implicit_flags=_cli_implicit_flags,
                _cli_ignore_unknown_args=_cli_ignore_unknown_args,
                _cli_kebab_case=_cli_kebab_case,
                _cli_shortcuts=_cli_shortcuts,
                _secrets_dir=_secrets_dir,
            )
        )

```

```python
class SettingsConfigDict(ConfigDict, total=False):
    case_sensitive: bool
    nested_model_default_partial_update: bool | None
    env_prefix: str
    env_file: DotenvType | None
    env_file_encoding: str | None
    env_ignore_empty: bool
    env_nested_delimiter: str | None
    env_nested_max_split: int | None
    env_parse_none_str: str | None
    env_parse_enums: bool | None
    cli_prog_name: str | None
    cli_parse_args: bool | list[str] | tuple[str, ...] | None
    cli_parse_none_str: str | None
    cli_hide_none_type: bool
    cli_avoid_json: bool
    cli_enforce_required: bool
    cli_use_class_docs_for_groups: bool
    cli_exit_on_error: bool
    cli_prefix: str
    cli_flag_prefix_char: str
    cli_implicit_flags: bool | None
    cli_ignore_unknown_args: bool | None
    cli_kebab_case: bool | None
    cli_shortcuts: Mapping[str, str | list[str]] | None
    secrets_dir: PathType | None
    json_file: PathType | None
    json_file_encoding: str | None
    yaml_file: PathType | None
    yaml_file_encoding: str | None
    yaml_config_section: str | None
    """
    Specifies the top-level key in a YAML file from which to load the settings.
    If provided, the settings will be loaded from the nested section under this key.
    This is useful when the YAML file contains multiple configuration sections
    and you only want to load a specific subset into your settings model.
    """

    pyproject_toml_depth: int
    """
    Number of levels **up** from the current working directory to attempt to find a pyproject.toml
    file.

    This is only used when a pyproject.toml file is not found in the current working directory.
    """

    pyproject_toml_table_header: tuple[str, ...]
    """
    Header of the TOML table within a pyproject.toml file to use when filling variables.
    This is supplied as a `tuple[str, ...]` instead of a `str` to accommodate for headers
    containing a `.`.

    For example, `toml_table_header = ("tool", "my.tool", "foo")` can be used to fill variable
    values from a table with header `[tool."my.tool".foo]`.

    To use the root table, exclude this config setting or provide an empty tuple.
    """

    toml_file: PathType | None
    enable_decoding: bool

```

## Config Dict

```python
class ConfigDict(TypedDict, total=False):
    """A TypedDict for configuring Pydantic behaviour."""

    title: str | None
    """The title for the generated JSON schema, defaults to the model's name"""

    model_title_generator: Callable[[type], str] | None
    """A callable that takes a model class and returns the title for it. Defaults to `None`."""

    field_title_generator: Callable[[str, FieldInfo | ComputedFieldInfo], str] | None
    """A callable that takes a field's name and info and returns title for it. Defaults to `None`."""

    str_to_lower: bool
    """Whether to convert all characters to lowercase for str types. Defaults to `False`."""

    str_to_upper: bool
    """Whether to convert all characters to uppercase for str types. Defaults to `False`."""

    str_strip_whitespace: bool
    """Whether to strip leading and trailing whitespace for str types."""

    str_min_length: int
    """The minimum length for str types. Defaults to `None`."""

    str_max_length: int | None
    """The maximum length for str types. Defaults to `None`."""

    extra: ExtraValues | None
    '''
    Whether to ignore, allow, or forbid extra data during model initialization. Defaults to `'ignore'`.

    Three configuration values are available:

    - `'ignore'`: Providing extra data is ignored (the default):
      ```python
      from pydantic import BaseModel, ConfigDict

      class User(BaseModel):
          model_config = ConfigDict(extra='ignore')  # (1)!

          name: str

      user = User(name='John Doe', age=20)  # (2)!
      print(user)
      #> name='John Doe'
      ```

        1. This is the default behaviour.
        2. The `age` argument is ignored.

    - `'forbid'`: Providing extra data is not permitted, and a [`ValidationError`][pydantic_core.ValidationError]
      will be raised if this is the case:
      ```python
      from pydantic import BaseModel, ConfigDict, ValidationError

      class Model(BaseModel):
          x: int

          model_config = ConfigDict(extra='forbid')

      try:
          Model(x=1, y='a')
      except ValidationError as exc:
          print(exc)
          """
          1 validation error for Model
          y
            Extra inputs are not permitted [type=extra_forbidden, input_value='a', input_type=str]
          """
      ```

    - `'allow'`: Providing extra data is allowed and stored in the `__pydantic_extra__` dictionary attribute:
      ```python
      from pydantic import BaseModel, ConfigDict

      class Model(BaseModel):
          x: int

          model_config = ConfigDict(extra='allow')

      m = Model(x=1, y='a')
      assert m.__pydantic_extra__ == {'y': 'a'}
      ```
      By default, no validation will be applied to these extra items, but you can set a type for the values by overriding
      the type annotation for `__pydantic_extra__`:
      ```python
      from pydantic import BaseModel, ConfigDict, Field, ValidationError

      class Model(BaseModel):
          __pydantic_extra__: dict[str, int] = Field(init=False)  # (1)!

          x: int

          model_config = ConfigDict(extra='allow')

      try:
          Model(x=1, y='a')
      except ValidationError as exc:
          print(exc)
          """
          1 validation error for Model
          y
            Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
          """

      m = Model(x=1, y='2')
      assert m.x == 1
      assert m.y == 2
      assert m.model_dump() == {'x': 1, 'y': 2}
      assert m.__pydantic_extra__ == {'y': 2}
      ```

        1. The `= Field(init=False)` does not have any effect at runtime, but prevents the `__pydantic_extra__` field from
           being included as a parameter to the model's `__init__` method by type checkers.

    As well as specifying an `extra` configuration value on the model, you can also provide it as an argument to the validation methods.
    This will override any `extra` configuration value set on the model:
    ```python
    from pydantic import BaseModel, ConfigDict, ValidationError

    class Model(BaseModel):
        x: int
        model_config = ConfigDict(extra="allow")

    try:
        # Override model config and forbid extra fields just this time
        Model.model_validate({"x": 1, "y": 2}, extra="forbid")
    except ValidationError as exc:
        print(exc)
        """
        1 validation error for Model
        y
          Extra inputs are not permitted [type=extra_forbidden, input_value=2, input_type=int]
        """
    ```
    '''

    frozen: bool
    """
    Whether models are faux-immutable, i.e. whether `__setattr__` is allowed, and also generates
    a `__hash__()` method for the model. This makes instances of the model potentially hashable if all the
    attributes are hashable. Defaults to `False`.

    Note:
        On V1, the inverse of this setting was called `allow_mutation`, and was `True` by default.
    """

    populate_by_name: bool
    """
    Whether an aliased field may be populated by its name as given by the model
    attribute, as well as the alias. Defaults to `False`.

    !!! warning
        `populate_by_name` usage is not recommended in v2.11+ and will be deprecated in v3.
        Instead, you should use the [`validate_by_name`][pydantic.config.ConfigDict.validate_by_name] configuration setting.

        When `validate_by_name=True` and `validate_by_alias=True`, this is strictly equivalent to the
        previous behavior of `populate_by_name=True`.

        In v2.11, we also introduced a [`validate_by_alias`][pydantic.config.ConfigDict.validate_by_alias] setting that introduces more fine grained
        control for validation behavior.

        Here's how you might go about using the new settings to achieve the same behavior:

        ```python
        from pydantic import BaseModel, ConfigDict, Field

        class Model(BaseModel):
            model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

            my_field: str = Field(alias='my_alias')  # (1)!

        m = Model(my_alias='foo')  # (2)!
        print(m)
        #> my_field='foo'

        m = Model(my_field='foo')  # (3)!
        print(m)
        #> my_field='foo'
        ```

        1. The field `'my_field'` has an alias `'my_alias'`.
        2. The model is populated by the alias `'my_alias'`.
        3. The model is populated by the attribute name `'my_field'`.
    """

    use_enum_values: bool
    """
    Whether to populate models with the `value` property of enums, rather than the raw enum.
    This may be useful if you want to serialize `model.model_dump()` later. Defaults to `False`.

    !!! note
        If you have an `Optional[Enum]` value that you set a default for, you need to use `validate_default=True`
        for said Field to ensure that the `use_enum_values` flag takes effect on the default, as extracting an
        enum's value occurs during validation, not serialization.

    ```python
    from enum import Enum
    from typing import Optional

    from pydantic import BaseModel, ConfigDict, Field

    class SomeEnum(Enum):
        FOO = 'foo'
        BAR = 'bar'
        BAZ = 'baz'

    class SomeModel(BaseModel):
        model_config = ConfigDict(use_enum_values=True)

        some_enum: SomeEnum
        another_enum: Optional[SomeEnum] = Field(
            default=SomeEnum.FOO, validate_default=True
        )

    model1 = SomeModel(some_enum=SomeEnum.BAR)
    print(model1.model_dump())
    #> {'some_enum': 'bar', 'another_enum': 'foo'}

    model2 = SomeModel(some_enum=SomeEnum.BAR, another_enum=SomeEnum.BAZ)
    print(model2.model_dump())
    #> {'some_enum': 'bar', 'another_enum': 'baz'}
    ```
    """

    validate_assignment: bool
    """
    Whether to validate the data when the model is changed. Defaults to `False`.

    The default behavior of Pydantic is to validate the data when the model is created.

    In case the user changes the data after the model is created, the model is _not_ revalidated.

    ```python
    from pydantic import BaseModel

    class User(BaseModel):
        name: str

    user = User(name='John Doe')  # (1)!
    print(user)
    #> name='John Doe'
    user.name = 123  # (1)!
    print(user)
    #> name=123
    ```

    1. The validation happens only when the model is created.
    2. The validation does not happen when the data is changed.

    In case you want to revalidate the model when the data is changed, you can use `validate_assignment=True`:

    ```python
    from pydantic import BaseModel, ValidationError

    class User(BaseModel, validate_assignment=True):  # (1)!
        name: str

    user = User(name='John Doe')  # (2)!
    print(user)
    #> name='John Doe'
    try:
        user.name = 123  # (3)!
    except ValidationError as e:
        print(e)
        '''
        1 validation error for User
        name
          Input should be a valid string [type=string_type, input_value=123, input_type=int]
        '''
    ```

    1. You can either use class keyword arguments, or `model_config` to set `validate_assignment=True`.
    2. The validation happens when the model is created.
    3. The validation _also_ happens when the data is changed.
    """

    arbitrary_types_allowed: bool
    """
    Whether arbitrary types are allowed for field types. Defaults to `False`.

    ```python
    from pydantic import BaseModel, ConfigDict, ValidationError

    # This is not a pydantic model, it's an arbitrary class
    class Pet:
        def __init__(self, name: str):
            self.name = name

    class Model(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)

        pet: Pet
        owner: str

    pet = Pet(name='Hedwig')
    # A simple check of instance type is used to validate the data
    model = Model(owner='Harry', pet=pet)
    print(model)
    #> pet=<__main__.Pet object at 0x0123456789ab> owner='Harry'
    print(model.pet)
    #> <__main__.Pet object at 0x0123456789ab>
    print(model.pet.name)
    #> Hedwig
    print(type(model.pet))
    #> <class '__main__.Pet'>
    try:
        # If the value is not an instance of the type, it's invalid
        Model(owner='Harry', pet='Hedwig')
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Model
        pet
          Input should be an instance of Pet [type=is_instance_of, input_value='Hedwig', input_type=str]
        '''

    # Nothing in the instance of the arbitrary type is checked
    # Here name probably should have been a str, but it's not validated
    pet2 = Pet(name=42)
    model2 = Model(owner='Harry', pet=pet2)
    print(model2)
    #> pet=<__main__.Pet object at 0x0123456789ab> owner='Harry'
    print(model2.pet)
    #> <__main__.Pet object at 0x0123456789ab>
    print(model2.pet.name)
    #> 42
    print(type(model2.pet))
    #> <class '__main__.Pet'>
    ```
    """

    from_attributes: bool
    """
    Whether to build models and look up discriminators of tagged unions using python object attributes.
    """

    loc_by_alias: bool
    """Whether to use the actual key provided in the data (e.g. alias) for error `loc`s rather than the field's name. Defaults to `True`."""

    alias_generator: Callable[[str], str] | AliasGenerator | None
    """
    A callable that takes a field name and returns an alias for it
    or an instance of [`AliasGenerator`][pydantic.aliases.AliasGenerator]. Defaults to `None`.

    When using a callable, the alias generator is used for both validation and serialization.
    If you want to use different alias generators for validation and serialization, you can use
    [`AliasGenerator`][pydantic.aliases.AliasGenerator] instead.

    If data source field names do not match your code style (e.g. CamelCase fields),
    you can automatically generate aliases using `alias_generator`. Here's an example with
    a basic callable:

    ```python
    from pydantic import BaseModel, ConfigDict
    from pydantic.alias_generators import to_pascal

    class Voice(BaseModel):
        model_config = ConfigDict(alias_generator=to_pascal)

        name: str
        language_code: str

    voice = Voice(Name='Filiz', LanguageCode='tr-TR')
    print(voice.language_code)
    #> tr-TR
    print(voice.model_dump(by_alias=True))
    #> {'Name': 'Filiz', 'LanguageCode': 'tr-TR'}
    ```

    If you want to use different alias generators for validation and serialization, you can use
    [`AliasGenerator`][pydantic.aliases.AliasGenerator].

    ```python
    from pydantic import AliasGenerator, BaseModel, ConfigDict
    from pydantic.alias_generators import to_camel, to_pascal

    class Athlete(BaseModel):
        first_name: str
        last_name: str
        sport: str

        model_config = ConfigDict(
            alias_generator=AliasGenerator(
                validation_alias=to_camel,
                serialization_alias=to_pascal,
            )
        )

    athlete = Athlete(firstName='John', lastName='Doe', sport='track')
    print(athlete.model_dump(by_alias=True))
    #> {'FirstName': 'John', 'LastName': 'Doe', 'Sport': 'track'}
    ```

    Note:
        Pydantic offers three built-in alias generators: [`to_pascal`][pydantic.alias_generators.to_pascal],
        [`to_camel`][pydantic.alias_generators.to_camel], and [`to_snake`][pydantic.alias_generators.to_snake].
    """

    ignored_types: tuple[type, ...]
    """A tuple of types that may occur as values of class attributes without annotations. This is
    typically used for custom descriptors (classes that behave like `property`). If an attribute is set on a
    class without an annotation and has a type that is not in this tuple (or otherwise recognized by
    _pydantic_), an error will be raised. Defaults to `()`.
    """

    allow_inf_nan: bool
    """Whether to allow infinity (`+inf` an `-inf`) and NaN values to float and decimal fields. Defaults to `True`."""

    json_schema_extra: JsonDict | JsonSchemaExtraCallable | None
    """A dict or callable to provide extra JSON schema properties. Defaults to `None`."""

    json_encoders: dict[type[object], JsonEncoder] | None
    """
    A `dict` of custom JSON encoders for specific types. Defaults to `None`.

    !!! warning "Deprecated"
        This config option is a carryover from v1.
        We originally planned to remove it in v2 but didn't have a 1:1 replacement so we are keeping it for now.
        It is still deprecated and will likely be removed in the future.
    """

    # new in V2
    strict: bool
    """
    _(new in V2)_ If `True`, strict validation is applied to all fields on the model.

    By default, Pydantic attempts to coerce values to the correct type, when possible.

    There are situations in which you may want to disable this behavior, and instead raise an error if a value's type
    does not match the field's type annotation.

    To configure strict mode for all fields on a model, you can set `strict=True` on the model.

    ```python
    from pydantic import BaseModel, ConfigDict

    class Model(BaseModel):
        model_config = ConfigDict(strict=True)

        name: str
        age: int
    ```

    See [Strict Mode](../concepts/strict_mode.md) for more details.

    See the [Conversion Table](../concepts/conversion_table.md) for more details on how Pydantic converts data in both
    strict and lax modes.
    """
    # whether instances of models and dataclasses (including subclass instances) should re-validate, default 'never'
    revalidate_instances: Literal['always', 'never', 'subclass-instances']
    """
    When and how to revalidate models and dataclasses during validation. Accepts the string
    values of `'never'`, `'always'` and `'subclass-instances'`. Defaults to `'never'`.

    - `'never'` will not revalidate models and dataclasses during validation
    - `'always'` will revalidate models and dataclasses during validation
    - `'subclass-instances'` will revalidate models and dataclasses during validation if the instance is a
        subclass of the model or dataclass

    By default, model and dataclass instances are not revalidated during validation.

    ```python
    from pydantic import BaseModel

    class User(BaseModel, revalidate_instances='never'):  # (1)!
        hobbies: list[str]

    class SubUser(User):
        sins: list[str]

    class Transaction(BaseModel):
        user: User

    my_user = User(hobbies=['reading'])
    t = Transaction(user=my_user)
    print(t)
    #> user=User(hobbies=['reading'])

    my_user.hobbies = [1]  # (2)!
    t = Transaction(user=my_user)  # (3)!
    print(t)
    #> user=User(hobbies=[1])

    my_sub_user = SubUser(hobbies=['scuba diving'], sins=['lying'])
    t = Transaction(user=my_sub_user)
    print(t)
    #> user=SubUser(hobbies=['scuba diving'], sins=['lying'])
    ```

    1. `revalidate_instances` is set to `'never'` by **default.
    2. The assignment is not validated, unless you set `validate_assignment` to `True` in the model's config.
    3. Since `revalidate_instances` is set to `never`, this is not revalidated.

    If you want to revalidate instances during validation, you can set `revalidate_instances` to `'always'`
    in the model's config.

    ```python
    from pydantic import BaseModel, ValidationError

    class User(BaseModel, revalidate_instances='always'):  # (1)!
        hobbies: list[str]

    class SubUser(User):
        sins: list[str]

    class Transaction(BaseModel):
        user: User

    my_user = User(hobbies=['reading'])
    t = Transaction(user=my_user)
    print(t)
    #> user=User(hobbies=['reading'])

    my_user.hobbies = [1]
    try:
        t = Transaction(user=my_user)  # (2)!
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Transaction
        user.hobbies.0
          Input should be a valid string [type=string_type, input_value=1, input_type=int]
        '''

    my_sub_user = SubUser(hobbies=['scuba diving'], sins=['lying'])
    t = Transaction(user=my_sub_user)
    print(t)  # (3)!
    #> user=User(hobbies=['scuba diving'])
    ```

    1. `revalidate_instances` is set to `'always'`.
    2. The model is revalidated, since `revalidate_instances` is set to `'always'`.
    3. Using `'never'` we would have gotten `user=SubUser(hobbies=['scuba diving'], sins=['lying'])`.

    It's also possible to set `revalidate_instances` to `'subclass-instances'` to only revalidate instances
    of subclasses of the model.

    ```python
    from pydantic import BaseModel

    class User(BaseModel, revalidate_instances='subclass-instances'):  # (1)!
        hobbies: list[str]

    class SubUser(User):
        sins: list[str]

    class Transaction(BaseModel):
        user: User

    my_user = User(hobbies=['reading'])
    t = Transaction(user=my_user)
    print(t)
    #> user=User(hobbies=['reading'])

    my_user.hobbies = [1]
    t = Transaction(user=my_user)  # (2)!
    print(t)
    #> user=User(hobbies=[1])

    my_sub_user = SubUser(hobbies=['scuba diving'], sins=['lying'])
    t = Transaction(user=my_sub_user)
    print(t)  # (3)!
    #> user=User(hobbies=['scuba diving'])
    ```

    1. `revalidate_instances` is set to `'subclass-instances'`.
    2. This is not revalidated, since `my_user` is not a subclass of `User`.
    3. Using `'never'` we would have gotten `user=SubUser(hobbies=['scuba diving'], sins=['lying'])`.
    """

    ser_json_timedelta: Literal['iso8601', 'float']
    """
    The format of JSON serialized timedeltas. Accepts the string values of `'iso8601'` and
    `'float'`. Defaults to `'iso8601'`.

    - `'iso8601'` will serialize timedeltas to [ISO 8601 text format](https://en.wikipedia.org/wiki/ISO_8601#Durations).
    - `'float'` will serialize timedeltas to the total number of seconds.

    !!! warning
        Starting in v2.12, it is recommended to use the [`ser_json_temporal`][pydantic.config.ConfigDict.ser_json_temporal]
        setting instead of `ser_json_timedelta`. This setting will be deprecated in v3.
    """

    ser_json_temporal: Literal['iso8601', 'seconds', 'milliseconds']
    """
    The format of JSON serialized temporal types from the [`datetime`][] module. This includes:

    - [`datetime.datetime`][]
    - [`datetime.date`][]
    - [`datetime.time`][]
    - [`datetime.timedelta`][]

    Can be one of:

    - `'iso8601'` will serialize date-like types to [ISO 8601 text format](https://en.wikipedia.org/wiki/ISO_8601#Durations).
    - `'milliseconds'` will serialize date-like types to a floating point number of milliseconds since the epoch.
    - `'seconds'` will serialize date-like types to a floating point number of seconds since the epoch.

    Defaults to `'iso8601'`.

    !!! note
        This setting was introduced in v2.12. It overlaps with the [`ser_json_timedelta`][pydantic.config.ConfigDict.ser_json_timedelta]
        setting which will be deprecated in v3. It also adds more configurability for
        the other temporal types.
    """

    val_temporal_unit: Literal['seconds', 'milliseconds', 'infer']
    """
    The unit to assume for validating numeric input for datetime-like types ([`datetime.datetime`][] and [`datetime.date`][]). Can be one of:

    - `'seconds'` will validate date or time numeric inputs as seconds since the [epoch].
    - `'milliseconds'` will validate date or time numeric inputs as milliseconds since the [epoch].
    - `'infer'` will infer the unit from the string numeric input on unix time as:

        * seconds since the [epoch] if $-2^{10} <= v <= 2^{10}$
        * milliseconds since the [epoch] (if $v < -2^{10}$ or $v > 2^{10}$).

    Defaults to `'infer'`.

    [epoch]: https://en.wikipedia.org/wiki/Unix_time
    """

    ser_json_bytes: Literal['utf8', 'base64', 'hex']
    """
    The encoding of JSON serialized bytes. Defaults to `'utf8'`.
    Set equal to `val_json_bytes` to get back an equal value after serialization round trip.

    - `'utf8'` will serialize bytes to UTF-8 strings.
    - `'base64'` will serialize bytes to URL safe base64 strings.
    - `'hex'` will serialize bytes to hexadecimal strings.
    """

    val_json_bytes: Literal['utf8', 'base64', 'hex']
    """
    The encoding of JSON serialized bytes to decode. Defaults to `'utf8'`.
    Set equal to `ser_json_bytes` to get back an equal value after serialization round trip.

    - `'utf8'` will deserialize UTF-8 strings to bytes.
    - `'base64'` will deserialize URL safe base64 strings to bytes.
    - `'hex'` will deserialize hexadecimal strings to bytes.
    """

    ser_json_inf_nan: Literal['null', 'constants', 'strings']
    """
    The encoding of JSON serialized infinity and NaN float values. Defaults to `'null'`.

    - `'null'` will serialize infinity and NaN values as `null`.
    - `'constants'` will serialize infinity and NaN values as `Infinity` and `NaN`.
    - `'strings'` will serialize infinity as string `"Infinity"` and NaN as string `"NaN"`.
    """

    # whether to validate default values during validation, default False
    validate_default: bool
    """Whether to validate default values during validation. Defaults to `False`."""

    validate_return: bool
    """Whether to validate the return value from call validators. Defaults to `False`."""

    protected_namespaces: tuple[str | Pattern[str], ...]
    """
    A `tuple` of strings and/or patterns that prevent models from having fields with names that conflict with them.
    For strings, we match on a prefix basis. Ex, if 'dog' is in the protected namespace, 'dog_name' will be protected.
    For patterns, we match on the entire field name. Ex, if `re.compile(r'^dog$')` is in the protected namespace, 'dog' will be protected, but 'dog_name' will not be.
    Defaults to `('model_validate', 'model_dump',)`.

    The reason we've selected these is to prevent collisions with other validation / dumping formats
    in the future - ex, `model_validate_{some_newly_supported_format}`.

    Before v2.10, Pydantic used `('model_',)` as the default value for this setting to
    prevent collisions between model attributes and `BaseModel`'s own methods. This was changed
    in v2.10 given feedback that this restriction was limiting in AI and data science contexts,
    where it is common to have fields with names like `model_id`, `model_input`, `model_output`, etc.

    For more details, see https://github.com/pydantic/pydantic/issues/10315.

    ```python
    import warnings

    from pydantic import BaseModel

    warnings.filterwarnings('error')  # Raise warnings as errors

    try:

        class Model(BaseModel):
            model_dump_something: str

    except UserWarning as e:
        print(e)
        '''
        Field 'model_dump_something' in 'Model' conflicts with protected namespace 'model_dump'.

        You may be able to solve this by setting the 'protected_namespaces' configuration to ('model_validate',).
        '''
    ```

    You can customize this behavior using the `protected_namespaces` setting:

    ```python {test="skip"}
    import re
    import warnings

    from pydantic import BaseModel, ConfigDict

    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter('always')  # Catch all warnings

        class Model(BaseModel):
            safe_field: str
            also_protect_field: str
            protect_this: str

            model_config = ConfigDict(
                protected_namespaces=(
                    'protect_me_',
                    'also_protect_',
                    re.compile('^protect_this$'),
                )
            )

    for warning in caught_warnings:
        print(f'{warning.message}')
        '''
        Field 'also_protect_field' in 'Model' conflicts with protected namespace 'also_protect_'.
        You may be able to solve this by setting the 'protected_namespaces' configuration to ('protect_me_', re.compile('^protect_this$'))`.

        Field 'protect_this' in 'Model' conflicts with protected namespace 're.compile('^protect_this$')'.
        You may be able to solve this by setting the 'protected_namespaces' configuration to ('protect_me_', 'also_protect_')`.
        '''
    ```

    While Pydantic will only emit a warning when an item is in a protected namespace but does not actually have a collision,
    an error _is_ raised if there is an actual collision with an existing attribute:

    ```python
    from pydantic import BaseModel, ConfigDict

    try:

        class Model(BaseModel):
            model_validate: str

            model_config = ConfigDict(protected_namespaces=('model_',))

    except ValueError as e:
        print(e)
        '''
        Field 'model_validate' conflicts with member <bound method BaseModel.model_validate of <class 'pydantic.main.BaseModel'>> of protected namespace 'model_'.
        '''
    ```
    """

    hide_input_in_errors: bool
    """
    Whether to hide inputs when printing errors. Defaults to `False`.

    Pydantic shows the input value and type when it raises `ValidationError` during the validation.

    ```python
    from pydantic import BaseModel, ValidationError

    class Model(BaseModel):
        a: str

    try:
        Model(a=123)
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Model
        a
          Input should be a valid string [type=string_type, input_value=123, input_type=int]
        '''
    ```

    You can hide the input value and type by setting the `hide_input_in_errors` config to `True`.

    ```python
    from pydantic import BaseModel, ConfigDict, ValidationError

    class Model(BaseModel):
        a: str
        model_config = ConfigDict(hide_input_in_errors=True)

    try:
        Model(a=123)
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Model
        a
          Input should be a valid string [type=string_type]
        '''
    ```
    """

    defer_build: bool
    """
    Whether to defer model validator and serializer construction until the first model validation. Defaults to False.

    This can be useful to avoid the overhead of building models which are only
    used nested within other models, or when you want to manually define type namespace via
    [`Model.model_rebuild(_types_namespace=...)`][pydantic.BaseModel.model_rebuild].

    Since v2.10, this setting also applies to pydantic dataclasses and TypeAdapter instances.
    """

    plugin_settings: dict[str, object] | None
    """A `dict` of settings for plugins. Defaults to `None`."""

    schema_generator: type[_GenerateSchema] | None
    """
    !!! warning
        `schema_generator` is deprecated in v2.10.

        Prior to v2.10, this setting was advertised as highly subject to change.
        It's possible that this interface may once again become public once the internal core schema generation
        API is more stable, but that will likely come after significant performance improvements have been made.
    """

    json_schema_serialization_defaults_required: bool
    """
    Whether fields with default values should be marked as required in the serialization schema. Defaults to `False`.

    This ensures that the serialization schema will reflect the fact a field with a default will always be present
    when serializing the model, even though it is not required for validation.

    However, there are scenarios where this may be undesirable — in particular, if you want to share the schema
    between validation and serialization, and don't mind fields with defaults being marked as not required during
    serialization. See [#7209](https://github.com/pydantic/pydantic/issues/7209) for more details.

    ```python
    from pydantic import BaseModel, ConfigDict

    class Model(BaseModel):
        a: str = 'a'

        model_config = ConfigDict(json_schema_serialization_defaults_required=True)

    print(Model.model_json_schema(mode='validation'))
    '''
    {
        'properties': {'a': {'default': 'a', 'title': 'A', 'type': 'string'}},
        'title': 'Model',
        'type': 'object',
    }
    '''
    print(Model.model_json_schema(mode='serialization'))
    '''
    {
        'properties': {'a': {'default': 'a', 'title': 'A', 'type': 'string'}},
        'required': ['a'],
        'title': 'Model',
        'type': 'object',
    }
    '''
    ```
    """

    json_schema_mode_override: Literal['validation', 'serialization', None]
    """
    If not `None`, the specified mode will be used to generate the JSON schema regardless of what `mode` was passed to
    the function call. Defaults to `None`.

    This provides a way to force the JSON schema generation to reflect a specific mode, e.g., to always use the
    validation schema.

    It can be useful when using frameworks (such as FastAPI) that may generate different schemas for validation
    and serialization that must both be referenced from the same schema; when this happens, we automatically append
    `-Input` to the definition reference for the validation schema and `-Output` to the definition reference for the
    serialization schema. By specifying a `json_schema_mode_override` though, this prevents the conflict between
    the validation and serialization schemas (since both will use the specified schema), and so prevents the suffixes
    from being added to the definition references.

    ```python
    from pydantic import BaseModel, ConfigDict, Json

    class Model(BaseModel):
        a: Json[int]  # requires a string to validate, but will dump an int

    print(Model.model_json_schema(mode='serialization'))
    '''
    {
        'properties': {'a': {'title': 'A', 'type': 'integer'}},
        'required': ['a'],
        'title': 'Model',
        'type': 'object',
    }
    '''

    class ForceInputModel(Model):
        # the following ensures that even with mode='serialization', we
        # will get the schema that would be generated for validation.
        model_config = ConfigDict(json_schema_mode_override='validation')

    print(ForceInputModel.model_json_schema(mode='serialization'))
    '''
    {
        'properties': {
            'a': {
                'contentMediaType': 'application/json',
                'contentSchema': {'type': 'integer'},
                'title': 'A',
                'type': 'string',
            }
        },
        'required': ['a'],
        'title': 'ForceInputModel',
        'type': 'object',
    }
    '''
    ```
    """

    coerce_numbers_to_str: bool
    """
    If `True`, enables automatic coercion of any `Number` type to `str` in "lax" (non-strict) mode. Defaults to `False`.

    Pydantic doesn't allow number types (`int`, `float`, `Decimal`) to be coerced as type `str` by default.

    ```python
    from decimal import Decimal

    from pydantic import BaseModel, ConfigDict, ValidationError

    class Model(BaseModel):
        value: str

    try:
        print(Model(value=42))
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Model
        value
          Input should be a valid string [type=string_type, input_value=42, input_type=int]
        '''

    class Model(BaseModel):
        model_config = ConfigDict(coerce_numbers_to_str=True)

        value: str

    repr(Model(value=42).value)
    #> "42"
    repr(Model(value=42.13).value)
    #> "42.13"
    repr(Model(value=Decimal('42.13')).value)
    #> "42.13"
    ```
    """

    regex_engine: Literal['rust-regex', 'python-re']
    """
    The regex engine to be used for pattern validation.
    Defaults to `'rust-regex'`.

    - `'rust-regex'` uses the [`regex`](https://docs.rs/regex) Rust crate,
      which is non-backtracking and therefore more DDoS resistant, but does not support all regex features.
    - `'python-re'` use the [`re`][] module, which supports all regex features, but may be slower.

    !!! note
        If you use a compiled regex pattern, the `'python-re'` engine will be used regardless of this setting.
        This is so that flags such as [`re.IGNORECASE`][] are respected.

    ```python
    from pydantic import BaseModel, ConfigDict, Field, ValidationError

    class Model(BaseModel):
        model_config = ConfigDict(regex_engine='python-re')

        value: str = Field(pattern=r'^abc(?=def)')

    print(Model(value='abcdef').value)
    #> abcdef

    try:
        print(Model(value='abxyzcdef'))
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Model
        value
          String should match pattern '^abc(?=def)' [type=string_pattern_mismatch, input_value='abxyzcdef', input_type=str]
        '''
    ```
    """

    validation_error_cause: bool
    """
    If `True`, Python exceptions that were part of a validation failure will be shown as an exception group as a cause. Can be useful for debugging. Defaults to `False`.

    Note:
        Python 3.10 and older don't support exception groups natively. <=3.10, backport must be installed: `pip install exceptiongroup`.

    Note:
        The structure of validation errors are likely to change in future Pydantic versions. Pydantic offers no guarantees about their structure. Should be used for visual traceback debugging only.
    """

    use_attribute_docstrings: bool
    '''
    Whether docstrings of attributes (bare string literals immediately following the attribute declaration)
    should be used for field descriptions. Defaults to `False`.

    Available in Pydantic v2.7+.

    ```python
    from pydantic import BaseModel, ConfigDict, Field

    class Model(BaseModel):
        model_config = ConfigDict(use_attribute_docstrings=True)

        x: str
        """
        Example of an attribute docstring
        """

        y: int = Field(description="Description in Field")
        """
        Description in Field overrides attribute docstring
        """

    print(Model.model_fields["x"].description)
    # > Example of an attribute docstring
    print(Model.model_fields["y"].description)
    # > Description in Field
    ```
    This requires the source code of the class to be available at runtime.

    !!! warning "Usage with `TypedDict` and stdlib dataclasses"
        Due to current limitations, attribute docstrings detection may not work as expected when using
        [`TypedDict`][typing.TypedDict] and stdlib dataclasses, in particular when:

        - inheritance is being used.
        - multiple classes have the same name in the same source file (unless Python 3.13 or greater is used).
    '''

    cache_strings: bool | Literal['all', 'keys', 'none']
    """
    Whether to cache strings to avoid constructing new Python objects. Defaults to True.

    Enabling this setting should significantly improve validation performance while increasing memory usage slightly.

    - `True` or `'all'` (the default): cache all strings
    - `'keys'`: cache only dictionary keys
    - `False` or `'none'`: no caching

    !!! note
        `True` or `'all'` is required to cache strings during general validation because
        validators don't know if they're in a key or a value.

    !!! tip
        If repeated strings are rare, it's recommended to use `'keys'` or `'none'` to reduce memory usage,
        as the performance difference is minimal if repeated strings are rare.
    """

    validate_by_alias: bool
    """
    Whether an aliased field may be populated by its alias. Defaults to `True`.

    !!! note
        In v2.11, `validate_by_alias` was introduced in conjunction with [`validate_by_name`][pydantic.ConfigDict.validate_by_name]
        to empower users with more fine grained validation control. In <v2.11, disabling validation by alias was not possible.

    Here's an example of disabling validation by alias:

    ```py
    from pydantic import BaseModel, ConfigDict, Field

    class Model(BaseModel):
        model_config = ConfigDict(validate_by_name=True, validate_by_alias=False)

        my_field: str = Field(validation_alias='my_alias')  # (1)!

    m = Model(my_field='foo')  # (2)!
    print(m)
    #> my_field='foo'
    ```

    1. The field `'my_field'` has an alias `'my_alias'`.
    2. The model can only be populated by the attribute name `'my_field'`.

    !!! warning
        You cannot set both `validate_by_alias` and `validate_by_name` to `False`.
        This would make it impossible to populate an attribute.

        See [usage errors](../errors/usage_errors.md#validate-by-alias-and-name-false) for an example.

        If you set `validate_by_alias` to `False`, under the hood, Pydantic dynamically sets
        `validate_by_name` to `True` to ensure that validation can still occur.
    """

    validate_by_name: bool
    """
    Whether an aliased field may be populated by its name as given by the model
    attribute. Defaults to `False`.

    !!! note
        In v2.0-v2.10, the `populate_by_name` configuration setting was used to specify
        whether or not a field could be populated by its name **and** alias.

        In v2.11, `validate_by_name` was introduced in conjunction with [`validate_by_alias`][pydantic.ConfigDict.validate_by_alias]
        to empower users with more fine grained validation behavior control.

    ```python
    from pydantic import BaseModel, ConfigDict, Field

    class Model(BaseModel):
        model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

        my_field: str = Field(validation_alias='my_alias')  # (1)!

    m = Model(my_alias='foo')  # (2)!
    print(m)
    #> my_field='foo'

    m = Model(my_field='foo')  # (3)!
    print(m)
    #> my_field='foo'
    ```

    1. The field `'my_field'` has an alias `'my_alias'`.
    2. The model is populated by the alias `'my_alias'`.
    3. The model is populated by the attribute name `'my_field'`.

    !!! warning
        You cannot set both `validate_by_alias` and `validate_by_name` to `False`.
        This would make it impossible to populate an attribute.

        See [usage errors](../errors/usage_errors.md#validate-by-alias-and-name-false) for an example.
    """

    serialize_by_alias: bool
    """
    Whether an aliased field should be serialized by its alias. Defaults to `False`.

    Note: In v2.11, `serialize_by_alias` was introduced to address the
    [popular request](https://github.com/pydantic/pydantic/issues/8379)
    for consistency with alias behavior for validation and serialization settings.
    In v3, the default value is expected to change to `True` for consistency with the validation default.

    ```python
    from pydantic import BaseModel, ConfigDict, Field

    class Model(BaseModel):
        model_config = ConfigDict(serialize_by_alias=True)

        my_field: str = Field(serialization_alias='my_alias')  # (1)!

    m = Model(my_field='foo')
    print(m.model_dump())  # (2)!
    #> {'my_alias': 'foo'}
    ```

    1. The field `'my_field'` has an alias `'my_alias'`.
    2. The model is serialized using the alias `'my_alias'` for the `'my_field'` attribute.
    """

    url_preserve_empty_path: bool
    """
    Whether to preserve empty URL paths when validating values for a URL type. Defaults to `False`.

    ```python
    from pydantic import AnyUrl, BaseModel, ConfigDict

    class Model(BaseModel):
        model_config = ConfigDict(url_preserve_empty_path=True)

        url: AnyUrl

    m = Model(url='http://example.com')
    print(m.url)
    #> http://example.com
    ```
    """
```

## Field

```python
def Field(  # noqa: C901
    default: Any = PydanticUndefined,
    *,
    default_factory: Callable[[], Any] | Callable[[dict[str, Any]], Any] | None = _Unset,
    alias: str | None = _Unset,
    alias_priority: int | None = _Unset,
    validation_alias: str | AliasPath | AliasChoices | None = _Unset,
    serialization_alias: str | None = _Unset,
    title: str | None = _Unset,
    field_title_generator: Callable[[str, FieldInfo], str] | None = _Unset,
    description: str | None = _Unset,
    examples: list[Any] | None = _Unset,
    exclude: bool | None = _Unset,
    exclude_if: Callable[[Any], bool] | None = _Unset,
    discriminator: str | types.Discriminator | None = _Unset,
    deprecated: Deprecated | str | bool | None = _Unset,
    json_schema_extra: JsonDict | Callable[[JsonDict], None] | None = _Unset,
    frozen: bool | None = _Unset,
    validate_default: bool | None = _Unset,
    repr: bool = _Unset,
    init: bool | None = _Unset,
    init_var: bool | None = _Unset,
    kw_only: bool | None = _Unset,
    pattern: str | re.Pattern[str] | None = _Unset,
    strict: bool | None = _Unset,
    coerce_numbers_to_str: bool | None = _Unset,
    gt: annotated_types.SupportsGt | None = _Unset,
    ge: annotated_types.SupportsGe | None = _Unset,
    lt: annotated_types.SupportsLt | None = _Unset,
    le: annotated_types.SupportsLe | None = _Unset,
    multiple_of: float | None = _Unset,
    allow_inf_nan: bool | None = _Unset,
    max_digits: int | None = _Unset,
    decimal_places: int | None = _Unset,
    min_length: int | None = _Unset,
    max_length: int | None = _Unset,
    union_mode: Literal['smart', 'left_to_right'] = _Unset,
    fail_fast: bool | None = _Unset,
    **extra: Unpack[_EmptyKwargs],
) -> Any:
    """!!! abstract "Usage Documentation"
        [Fields](../concepts/fields.md)

    Create a field for objects that can be configured.

    Used to provide extra information about a field, either for the model schema or complex validation. Some arguments
    apply only to number fields (`int`, `float`, `Decimal`) and some apply only to `str`.

    Note:
        - Any `_Unset` objects will be replaced by the corresponding value defined in the `_DefaultValues` dictionary. If a key for the `_Unset` object is not found in the `_DefaultValues` dictionary, it will default to `None`

    Args:
        default: Default value if the field is not set.
        default_factory: A callable to generate the default value. The callable can either take 0 arguments
            (in which case it is called as is) or a single argument containing the already validated data.
        alias: The name to use for the attribute when validating or serializing by alias.
            This is often used for things like converting between snake and camel case.
        alias_priority: Priority of the alias. This affects whether an alias generator is used.
        validation_alias: Like `alias`, but only affects validation, not serialization.
        serialization_alias: Like `alias`, but only affects serialization, not validation.
        title: Human-readable title.
        field_title_generator: A callable that takes a field name and returns title for it.
        description: Human-readable description.
        examples: Example values for this field.
        exclude: Whether to exclude the field from the model serialization.
        exclude_if: A callable that determines whether to exclude a field during serialization based on its value.
        discriminator: Field name or Discriminator for discriminating the type in a tagged union.
        deprecated: A deprecation message, an instance of `warnings.deprecated` or the `typing_extensions.deprecated` backport,
            or a boolean. If `True`, a default deprecation message will be emitted when accessing the field.
        json_schema_extra: A dict or callable to provide extra JSON schema properties.
        frozen: Whether the field is frozen. If true, attempts to change the value on an instance will raise an error.
        validate_default: If `True`, apply validation to the default value every time you create an instance.
            Otherwise, for performance reasons, the default value of the field is trusted and not validated.
        repr: A boolean indicating whether to include the field in the `__repr__` output.
        init: Whether the field should be included in the constructor of the dataclass.
            (Only applies to dataclasses.)
        init_var: Whether the field should _only_ be included in the constructor of the dataclass.
            (Only applies to dataclasses.)
        kw_only: Whether the field should be a keyword-only argument in the constructor of the dataclass.
            (Only applies to dataclasses.)
        coerce_numbers_to_str: Whether to enable coercion of any `Number` type to `str` (not applicable in `strict` mode).
        strict: If `True`, strict validation is applied to the field.
            See [Strict Mode](../concepts/strict_mode.md) for details.
        gt: Greater than. If set, value must be greater than this. Only applicable to numbers.
        ge: Greater than or equal. If set, value must be greater than or equal to this. Only applicable to numbers.
        lt: Less than. If set, value must be less than this. Only applicable to numbers.
        le: Less than or equal. If set, value must be less than or equal to this. Only applicable to numbers.
        multiple_of: Value must be a multiple of this. Only applicable to numbers.
        min_length: Minimum length for iterables.
        max_length: Maximum length for iterables.
        pattern: Pattern for strings (a regular expression).
        allow_inf_nan: Allow `inf`, `-inf`, `nan`. Only applicable to float and [`Decimal`][decimal.Decimal] numbers.
        max_digits: Maximum number of allow digits for strings.
        decimal_places: Maximum number of decimal places allowed for numbers.
        union_mode: The strategy to apply when validating a union. Can be `smart` (the default), or `left_to_right`.
            See [Union Mode](../concepts/unions.md#union-modes) for details.
        fail_fast: If `True`, validation will stop on the first error. If `False`, all validation errors will be collected.
            This option can be applied only to iterable types (list, tuple, set, and frozenset).
        extra: (Deprecated) Extra fields that will be included in the JSON schema.

            !!! warning Deprecated
                The `extra` kwargs is deprecated. Use `json_schema_extra` instead.

    Returns:
        A new [`FieldInfo`][pydantic.fields.FieldInfo]. The return annotation is `Any` so `Field` can be used on
            type-annotated fields without causing a type error.
    """
    # Check deprecated and removed params from V1. This logic should eventually be removed.
    const = extra.pop('const', None)  # type: ignore
    if const is not None:
        raise PydanticUserError('`const` is removed, use `Literal` instead', code='removed-kwargs')

    min_items = extra.pop('min_items', None)  # type: ignore
    if min_items is not None:
        warn(
            '`min_items` is deprecated and will be removed, use `min_length` instead',
            PydanticDeprecatedSince20,
            stacklevel=2,
        )
        if min_length in (None, _Unset):
            min_length = min_items  # type: ignore

    max_items = extra.pop('max_items', None)  # type: ignore
    if max_items is not None:
        warn(
            '`max_items` is deprecated and will be removed, use `max_length` instead',
            PydanticDeprecatedSince20,
            stacklevel=2,
        )
        if max_length in (None, _Unset):
            max_length = max_items  # type: ignore

    unique_items = extra.pop('unique_items', None)  # type: ignore
    if unique_items is not None:
        raise PydanticUserError(
            (
                '`unique_items` is removed, use `Set` instead'
                '(this feature is discussed in https://github.com/pydantic/pydantic-core/issues/296)'
            ),
            code='removed-kwargs',
        )

    allow_mutation = extra.pop('allow_mutation', None)  # type: ignore
    if allow_mutation is not None:
        warn(
            '`allow_mutation` is deprecated and will be removed. use `frozen` instead',
            PydanticDeprecatedSince20,
            stacklevel=2,
        )
        if allow_mutation is False:
            frozen = True

    regex = extra.pop('regex', None)  # type: ignore
    if regex is not None:
        raise PydanticUserError('`regex` is removed. use `pattern` instead', code='removed-kwargs')

    if extra:
        warn(
            'Using extra keyword arguments on `Field` is deprecated and will be removed.'
            ' Use `json_schema_extra` instead.'
            f' (Extra keys: {", ".join(k.__repr__() for k in extra.keys())})',
            PydanticDeprecatedSince20,
            stacklevel=2,
        )
        if not json_schema_extra or json_schema_extra is _Unset:
            json_schema_extra = extra  # type: ignore

    if (
        validation_alias
        and validation_alias is not _Unset
        and not isinstance(validation_alias, (str, AliasChoices, AliasPath))
    ):
        raise TypeError('Invalid `validation_alias` type. it should be `str`, `AliasChoices`, or `AliasPath`')

    if serialization_alias in (_Unset, None) and isinstance(alias, str):
        serialization_alias = alias

    if validation_alias in (_Unset, None):
        validation_alias = alias

    include = extra.pop('include', None)  # type: ignore
    if include is not None:
        warn(
            '`include` is deprecated and does nothing. It will be removed, use `exclude` instead',
            PydanticDeprecatedSince20,
            stacklevel=2,
        )

    return FieldInfo.from_field(
        default,
        default_factory=default_factory,
        alias=alias,
        alias_priority=alias_priority,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        title=title,
        field_title_generator=field_title_generator,
        description=description,
        examples=examples,
        exclude=exclude,
        exclude_if=exclude_if,
        discriminator=discriminator,
        deprecated=deprecated,
        json_schema_extra=json_schema_extra,
        frozen=frozen,
        pattern=pattern,
        validate_default=validate_default,
        repr=repr,
        init=init,
        init_var=init_var,
        kw_only=kw_only,
        coerce_numbers_to_str=coerce_numbers_to_str,
        strict=strict,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        multiple_of=multiple_of,
        min_length=min_length,
        max_length=max_length,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        union_mode=union_mode,
        fail_fast=fail_fast,
    )

```

## DeclartiveBase

```python
class DeclarativeBase(
    # Inspectable is used only by the mypy plugin
    inspection.Inspectable[InstanceState[Any]],
    metaclass=DeclarativeAttributeIntercept,
):
    """Base class used for declarative class definitions.

    The :class:`_orm.DeclarativeBase` allows for the creation of new
    declarative bases in such a way that is compatible with type checkers::

        from sqlalchemy.orm import DeclarativeBase

        class Base(DeclarativeBase):
            pass

    The above ``Base`` class is now usable as the base for new declarative
    mappings.  The superclass makes use of the ``__init_subclass__()``
    method to set up new classes and metaclasses aren't used.

    When first used, the :class:`_orm.DeclarativeBase` class instantiates a new
    :class:`_orm.registry` to be used with the base, assuming one was not
    provided explicitly. The :class:`_orm.DeclarativeBase` class supports
    class-level attributes which act as parameters for the construction of this
    registry; such as to indicate a specific :class:`_schema.MetaData`
    collection as well as a specific value for
    :paramref:`_orm.registry.type_annotation_map`::

        from typing_extensions import Annotated

        from sqlalchemy import BigInteger
        from sqlalchemy import MetaData
        from sqlalchemy import String
        from sqlalchemy.orm import DeclarativeBase

        bigint = Annotated[int, "bigint"]
        my_metadata = MetaData()

        class Base(DeclarativeBase):
            metadata = my_metadata
            type_annotation_map = {
                str: String().with_variant(String(255), "mysql", "mariadb"),
                bigint: BigInteger(),
            }

    Class-level attributes which may be specified include:

    :param metadata: optional :class:`_schema.MetaData` collection.
     If a :class:`_orm.registry` is constructed automatically, this
     :class:`_schema.MetaData` collection will be used to construct it.
     Otherwise, the local :class:`_schema.MetaData` collection will supercede
     that used by an existing :class:`_orm.registry` passed using the
     :paramref:`_orm.DeclarativeBase.registry` parameter.
    :param type_annotation_map: optional type annotation map that will be
     passed to the :class:`_orm.registry` as
     :paramref:`_orm.registry.type_annotation_map`.
    :param registry: supply a pre-existing :class:`_orm.registry` directly.

    .. versionadded:: 2.0  Added :class:`.DeclarativeBase`, so that declarative
       base classes may be constructed in such a way that is also recognized
       by :pep:`484` type checkers.   As a result, :class:`.DeclarativeBase`
       and other subclassing-oriented APIs should be seen as
       superseding previous "class returned by a function" APIs, namely
       :func:`_orm.declarative_base` and :meth:`_orm.registry.generate_base`,
       where the base class returned cannot be recognized by type checkers
       without using plugins.

    **__init__ behavior**

    In a plain Python class, the base-most ``__init__()`` method in the class
    hierarchy is ``object.__init__()``, which accepts no arguments. However,
    when the :class:`_orm.DeclarativeBase` subclass is first declared, the
    class is given an ``__init__()`` method that links to the
    :paramref:`_orm.registry.constructor` constructor function, if no
    ``__init__()`` method is already present; this is the usual declarative
    constructor that will assign keyword arguments as attributes on the
    instance, assuming those attributes are established at the class level
    (i.e. are mapped, or are linked to a descriptor). This constructor is
    **never accessed by a mapped class without being called explicitly via
    super()**, as mapped classes are themselves given an ``__init__()`` method
    directly which calls :paramref:`_orm.registry.constructor`, so in the
    default case works independently of what the base-most ``__init__()``
    method does.

    .. versionchanged:: 2.0.1  :class:`_orm.DeclarativeBase` has a default
       constructor that links to :paramref:`_orm.registry.constructor` by
       default, so that calls to ``super().__init__()`` can access this
       constructor. Previously, due to an implementation mistake, this default
       constructor was missing, and calling ``super().__init__()`` would invoke
       ``object.__init__()``.

    The :class:`_orm.DeclarativeBase` subclass may also declare an explicit
    ``__init__()`` method which will replace the use of the
    :paramref:`_orm.registry.constructor` function at this level::

        class Base(DeclarativeBase):
            def __init__(self, id=None):
                self.id = id

    Mapped classes still will not invoke this constructor implicitly; it
    remains only accessible by calling ``super().__init__()``::

        class MyClass(Base):
            def __init__(self, id=None, name=None):
                self.name = name
                super().__init__(id=id)

    Note that this is a different behavior from what functions like the legacy
    :func:`_orm.declarative_base` would do; the base created by those functions
    would always install :paramref:`_orm.registry.constructor` for
    ``__init__()``.

    """

    if typing.TYPE_CHECKING:

        def _sa_inspect_type(self) -> Mapper[Self]: ...

        def _sa_inspect_instance(self) -> InstanceState[Self]: ...

        _sa_registry: ClassVar[_RegistryType]

        registry: ClassVar[_RegistryType]
        """Refers to the :class:`_orm.registry` in use where new
        :class:`_orm.Mapper` objects will be associated."""

        metadata: ClassVar[MetaData]
        """Refers to the :class:`_schema.MetaData` collection that will be used
        for new :class:`_schema.Table` objects.

        .. seealso::

            :ref:`orm_declarative_metadata`

        """

        __name__: ClassVar[str]

        # this ideally should be Mapper[Self], but mypy as of 1.4.1 does not
        # like it, and breaks the declared_attr_one test. Pyright/pylance is
        # ok with it.
        __mapper__: ClassVar[Mapper[Any]]
        """The :class:`_orm.Mapper` object to which a particular class is
        mapped.

        May also be acquired using :func:`_sa.inspect`, e.g.
        ``inspect(klass)``.

        """

        __table__: ClassVar[FromClause]
        """The :class:`_sql.FromClause` to which a particular subclass is
        mapped.

        This is usually an instance of :class:`_schema.Table` but may also
        refer to other kinds of :class:`_sql.FromClause` such as
        :class:`_sql.Subquery`, depending on how the class is mapped.

        .. seealso::

            :ref:`orm_declarative_metadata`

        """

        # pyright/pylance do not consider a classmethod a ClassVar so use Any
        # https://github.com/microsoft/pylance-release/issues/3484
        __tablename__: Any
        """String name to assign to the generated
        :class:`_schema.Table` object, if not specified directly via
        :attr:`_orm.DeclarativeBase.__table__`.

        .. seealso::

            :ref:`orm_declarative_table`

        """

        __mapper_args__: Any
        """Dictionary of arguments which will be passed to the
        :class:`_orm.Mapper` constructor.

        .. seealso::

            :ref:`orm_declarative_mapper_options`

        """

        __table_args__: Any
        """A dictionary or tuple of arguments that will be passed to the
        :class:`_schema.Table` constructor.  See
        :ref:`orm_declarative_table_configuration`
        for background on the specific structure of this collection.

        .. seealso::

            :ref:`orm_declarative_table_configuration`

        """

        def __init__(self, **kw: Any): ...

    def __init_subclass__(cls, **kw: Any) -> None:
        if DeclarativeBase in cls.__bases__:
            _check_not_declarative(cls, DeclarativeBase)
            _setup_declarative_base(cls)
        else:
            _as_declarative(cls._sa_registry, cls, cls.__dict__)
        super().__init_subclass__(**kw)
```

## mapped_column

```python
def mapped_column(
    __name_pos: Optional[
        Union[str, _TypeEngineArgument[Any], SchemaEventTarget]
    ] = None,
    __type_pos: Optional[
        Union[_TypeEngineArgument[Any], SchemaEventTarget]
    ] = None,
    *args: SchemaEventTarget,
    init: Union[_NoArg, bool] = _NoArg.NO_ARG,
    repr: Union[_NoArg, bool] = _NoArg.NO_ARG,  # noqa: A002
    default: Optional[Any] = _NoArg.NO_ARG,
    default_factory: Union[_NoArg, Callable[[], _T]] = _NoArg.NO_ARG,
    compare: Union[_NoArg, bool] = _NoArg.NO_ARG,
    kw_only: Union[_NoArg, bool] = _NoArg.NO_ARG,
    hash: Union[_NoArg, bool, None] = _NoArg.NO_ARG,  # noqa: A002
    nullable: Optional[
        Union[bool, Literal[SchemaConst.NULL_UNSPECIFIED]]
    ] = SchemaConst.NULL_UNSPECIFIED,
    primary_key: Optional[bool] = False,
    deferred: Union[_NoArg, bool] = _NoArg.NO_ARG,
    deferred_group: Optional[str] = None,
    deferred_raiseload: Optional[bool] = None,
    use_existing_column: bool = False,
    name: Optional[str] = None,
    type_: Optional[_TypeEngineArgument[Any]] = None,
    autoincrement: _AutoIncrementType = "auto",
    doc: Optional[str] = None,
    key: Optional[str] = None,
    index: Optional[bool] = None,
    unique: Optional[bool] = None,
    info: Optional[_InfoType] = None,
    onupdate: Optional[Any] = None,
    insert_default: Optional[Any] = _NoArg.NO_ARG,
    server_default: Optional[_ServerDefaultArgument] = None,
    server_onupdate: Optional[_ServerOnUpdateArgument] = None,
    active_history: bool = False,
    quote: Optional[bool] = None,
    system: bool = False,
    comment: Optional[str] = None,
    sort_order: Union[_NoArg, int] = _NoArg.NO_ARG,
    dataclass_metadata: Union[_NoArg, Mapping[Any, Any], None] = _NoArg.NO_ARG,
    **kw: Any,
) -> MappedColumn[Any]:
```

## Fastapi

### app

```python
Query(
        default=default,
        default_factory=default_factory,
        alias=alias,
        alias_priority=alias_priority,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        regex=regex,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        example=example,
        examples=examples,
        openapi_examples=openapi_examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        json_schema_extra=json_schema_extra,
          
  
  Header(
        default=default,
        default_factory=default_factory,
        alias=alias,
        alias_priority=alias_priority,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        convert_underscores=convert_underscores,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        regex=regex,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        example=example,
        examples=examples,
        openapi_examples=openapi_examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        json_schema_extra=json_schema_extra,
        
 Cookie(
        default=default,
        default_factory=default_factory,
        alias=alias,
        alias_priority=alias_priority,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        regex=regex,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        example=example,
        examples=examples,
        openapi_examples=openapi_examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        json_schema_extra=json_schema_extra,
        
        
        
 
 Body(
        default=default,
        default_factory=default_factory,
        embed=embed,
        media_type=media_type,
        alias=alias,
        alias_priority=alias_priority,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        regex=regex,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        example=example,
        examples=examples,
        openapi_examples=openapi_examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        json_schema_extra=json_schema_extra,
        
        
        
        
  Form(
        default=default,
        default_factory=default_factory,
        media_type=media_type,
        alias=alias,
        alias_priority=alias_priority,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        regex=regex,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        example=example,
        examples=examples,
        openapi_examples=openapi_examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        json_schema_extra=json_schema_extra,
        
        
        
        
  File(
        default=default,
        default_factory=default_factory,
        media_type=media_type,
        alias=alias,
        alias_priority=alias_priority,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        regex=regex,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        example=example,
        examples=examples,
        openapi_examples=openapi_examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        json_schema_extra=json_schema_extra,
        
        
        
  Depends(  # noqa: N802
    dependency: Annotated[
        Optional[Callable[..., Any]],
        Doc(
            """
            A "dependable" callable (like a function).

            Don't call it directly, FastAPI will call it for you, just pass the object
            directly.
            """
        ),
    ] = None,
    *,
    use_cache: Annotated[
        bool,
        Doc(
            """
            By default, after a dependency is called the first time in a request, if
            the dependency is declared again for the rest of the request (for example
            if the dependency is needed by several dependencies), the value will be
            re-used for the rest of the request.

            Set `use_cache` to `False` to disable this behavior and ensure the
            dependency is called again (if declared more than once) in the same request.
            """
        ),
    ] = True,      
        
               
        
        
        
 Path(
        default=default,
        default_factory=default_factory,
        alias=alias,
        alias_priority=alias_priority,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        regex=regex,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        example=example,
        examples=examples,
        openapi_examples=openapi_examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        json_schema_extra=json_schema_extra,
        
        
        
```

### router

```python
class APIRoute(routing.Route):
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        response_model: Any = Default(None),
        status_code: Optional[int] = None,
        tags: Optional[List[Union[str, Enum]]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        name: Optional[str] = None,
        methods: Optional[Union[Set[str], List[str]]] = None,
        operation_id: Optional[str] = None,
        response_model_include: Optional[IncEx] = None,
        response_model_exclude: Optional[IncEx] = None,
        response_model_by_alias: bool = True,
        response_model_exclude_unset: bool = False,
        response_model_exclude_defaults: bool = False,
        response_model_exclude_none: bool = False,
        include_in_schema: bool = True,
        response_class: Union[Type[Response], DefaultPlaceholder] = Default(
            JSONResponse
        ),
        dependency_overrides_provider: Optional[Any] = None,
        callbacks: Optional[List[BaseRoute]] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
        generate_unique_id_function: Union[
            Callable[["APIRoute"], str], DefaultPlaceholder
        ] = Default(generate_unique_id),
        

 def include_router(
        self,
        router: Annotated["APIRouter", Doc("The `APIRouter` to include.")],
        *,
        prefix: Annotated[str, Doc("An optional path prefix for the router.")] = "",
        tags: Annotated[
            Optional[List[Union[str, Enum]]],
            Doc(
                """
                A list of tags to be applied to all the *path operations* in this
                router.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for Path Operation Configuration](https://fastapi.tiangolo.com/tutorial/path-operation-configuration/).
                """
            ),
        ] = None,
        dependencies: Annotated[
            Optional[Sequence[params.Depends]],
            Doc(
                """
                A list of dependencies (using `Depends()`) to be applied to all the
                *path operations* in this router.

                Read more about it in the
                [FastAPI docs for Bigger Applications - Multiple Files](https://fastapi.tiangolo.com/tutorial/bigger-applications/#include-an-apirouter-with-a-custom-prefix-tags-responses-and-dependencies).
                """
            ),
        ] = None,
        default_response_class: Annotated[
            Type[Response],
            Doc(
                """
                The default response class to be used.

                Read more in the
                [FastAPI docs for Custom Response - HTML, Stream, File, others](https://fastapi.tiangolo.com/advanced/custom-response/#default-response-class).
                """
            ),
        ] = Default(JSONResponse),
        responses: Annotated[
            Optional[Dict[Union[int, str], Dict[str, Any]]],
            Doc(
                """
                Additional responses to be shown in OpenAPI.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for Additional Responses in OpenAPI](https://fastapi.tiangolo.com/advanced/additional-responses/).

                And in the
                [FastAPI docs for Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/#include-an-apirouter-with-a-custom-prefix-tags-responses-and-dependencies).
                """
            ),
        ] = None,
        callbacks: Annotated[
            Optional[List[BaseRoute]],
            Doc(
                """
                OpenAPI callbacks that should apply to all *path operations* in this
                router.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for OpenAPI Callbacks](https://fastapi.tiangolo.com/advanced/openapi-callbacks/).
                """
            ),
        ] = None,
        deprecated: Annotated[
            Optional[bool],
            Doc(
                """
                Mark all *path operations* in this router as deprecated.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for Path Operation Configuration](https://fastapi.tiangolo.com/tutorial/path-operation-configuration/).
                """
            ),
        ] = None,
        include_in_schema: Annotated[
            bool,
            Doc(
                """
                Include (or not) all the *path operations* in this router in the
                generated OpenAPI schema.

                This affects the generated OpenAPI (e.g. visible at `/docs`).
                """
            ),
        ] = True,
        generate_unique_id_function: Annotated[
            Callable[[APIRoute], str],
            Doc(
                """
                Customize the function used to generate unique IDs for the *path
                operations* shown in the generated OpenAPI.

                This is particularly useful when automatically generating clients or
                SDKs for your API.

                Read more about it in the
                [FastAPI docs about how to Generate Clients](https://fastapi.tiangolo.com/advanced/generate-clients/#custom-generate-unique-id-function).
                """
            ),
        ] = Default(generate_unique_id),
    ) -> None:
        """
        Include another `APIRouter` in the same current `APIRouter`.

        Read more about it in the
        [FastAPI docs for Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/).

        ## Example

        ```python
        from fastapi import APIRouter, FastAPI

        app = FastAPI()
        internal_router = APIRouter()
        users_router = APIRouter()

        @users_router.get("/users/")
        def read_users():
            return [{"name": "Rick"}, {"name": "Morty"}]

        internal_router.include_router(users_router)
        app.include_router(internal_router)
        ```
        """
```