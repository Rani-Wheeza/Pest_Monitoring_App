from domain.validation import FieldError


class DomainValidationError(Exception):
    """One or more business rules failed. Views turn this into HTTP 400."""

    def __init__(self, errors: list[FieldError]):
        super().__init__("; ".join(f"{e.field}: {e.message}" for e in errors))
        self.errors = errors

    def as_dict(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for error in self.errors:
            out.setdefault(error.field, []).append(error.message)
        return out


class NotAllowedError(Exception):
    """The user may not do this to this sighting. Views turn this into HTTP 403."""
