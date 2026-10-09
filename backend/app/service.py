"""Resource operations and aggregate invariants, independent of HTTP routing."""

from datetime import datetime, timezone

from fastapi import HTTPException

from .schemas import MODELS

TABLES = set(MODELS) | {"resumes", "status_history"}


def now():
    return datetime.now(timezone.utc).isoformat()


def get(connection, table, record_id):
    if table not in TABLES:
        raise HTTPException(404, "Unknown resource")
    row = connection.execute(f"SELECT * FROM {table} WHERE id=?", (record_id,)).fetchone()
    if row is None:
        raise HTTPException(404, f"{table.rstrip('s').capitalize()} not found")
    return dict(row)


def country_of_application(connection, application_id):
    application = get(connection, "applications", application_id)
    return get(connection, "companies", application["company_id"])["country_id"]


def same_country(actual, expected):
    if actual != expected:
        raise HTTPException(422, "These records must belong to the same country")


def validate_links(connection, table, data, old=None):
    if "country_id" in data:
        get(connection, "countries", data["country_id"])
    if table == "applications":
        company = get(connection, "companies", data["company_id"])
        if data["resume_id"]:
            cv = get(connection, "resumes", data["resume_id"])
            same_country(cv["country_id"], company["country_id"])
        if old and old["company_id"] != data["company_id"]:
            raise HTTPException(422, "An existing application cannot be moved to another company")
    if table in ("companies", "contacts") and old and old["country_id"] != data["country_id"]:
        raise HTTPException(422, "An existing record cannot be moved between countries")
    if table == "contacts" and data["company_id"]:
        same_country(
            get(connection, "companies", data["company_id"])["country_id"],
            data["country_id"],
        )
    if table == "followups":
        if data["contact_id"]:
            same_country(
                get(connection, "contacts", data["contact_id"])["country_id"],
                data["country_id"],
            )
        if data["application_id"]:
            same_country(
                country_of_application(connection, data["application_id"]),
                data["country_id"],
            )
    if table == "interactions":
        contact = get(connection, "contacts", data["contact_id"])
        if data["application_id"]:
            same_country(
                country_of_application(connection, data["application_id"]),
                contact["country_id"],
            )
            application = get(connection, "applications", data["application_id"])
            if contact["company_id"] and contact["company_id"] != application["company_id"]:
                raise HTTPException(
                    422, "The contact and application must belong to the same company"
                )
    if table == "interviews":
        get(connection, "applications", data["application_id"])


def insert(connection, table, values):
    if table not in TABLES:
        raise HTTPException(404)
    columns = list(values)
    result = connection.execute(
        f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
        list(values.values()),
    )
    return get(connection, table, result.lastrowid)


def save(connection, table, payload, record_id=None):
    model = MODELS.get(table)
    if model is None:
        raise HTTPException(404, "Unknown resource")
    old = get(connection, table, record_id) if record_id else None
    combined = {key: value for key, value in (old or {}).items() if key in model.model_fields}
    combined.update(payload)
    data = model.model_validate(combined).model_dump(mode="json")
    validate_links(connection, table, data, old)
    stamp = now()
    if (
        table == "applications"
        and data["status"] not in ("Saved", "Contacted")
        and not data["date_applied"]
    ):
        data["date_applied"] = stamp[:10]
    if old:
        data["updated_at"] = stamp
        connection.execute(
            f"UPDATE {table} SET {','.join(f'{key}=?' for key in data)} WHERE id=?",
            [*data.values(), record_id],
        )
        result = get(connection, table, record_id)
    else:
        result = insert(connection, table, {**data, "created_at": stamp, "updated_at": stamp})
    if table == "applications" and (not old or old["status"] != data["status"]):
        insert(
            connection,
            "status_history",
            {
                "application_id": result["id"],
                "previous_status": old["status"] if old else None,
                "new_status": data["status"],
                "changed_at": stamp,
            },
        )
    if table == "interactions" and data["kind"] == "Reply received" and data["application_id"]:
        connection.execute(
            "UPDATE applications SET first_response_at=COALESCE(first_response_at,?), updated_at=? WHERE id=?",
            (data["occurred_at"][:10], stamp, data["application_id"]),
        )
    return result
