# The single schema every input file gets mapped into, regardless of which
# provider (PropStream, BatchLeads, ListSource, ...) it came from. Everything
# downstream (normalizing, deduping) only ever has to deal with this shape.
STANDARD_FIELDS = [
    "owner_first",
    "owner_last",
    "mail_address",
    "mail_city",
    "mail_state",
    "mail_zip",
    "property_address",
    "property_city",
    "property_state",
    "property_zip",
    "phone",
    "email",
]
