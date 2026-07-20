#!/usr/bin/env python3
from readiness_validation.consistency import ValidationError, validate


def main() -> int:
    try:
        validate()
    except ValidationError as exc:
        print(f"ERROR: {exc}")
        return 1
    print("Cross-document readiness consistency validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
