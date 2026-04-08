def serialize_mongo(doc):
    if not doc:
        return doc

    doc["_id"] = str(doc["_id"])

    # convert nested messages timestamps if needed
    if "messages" in doc:
        for msg in doc["messages"]:
            if "_id" in msg:
                msg["_id"] = str(msg["_id"])

    return doc