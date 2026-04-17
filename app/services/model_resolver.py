from models.model import MAImodel


def get_model(db, tenant_id):

    model = db.query(MAImodel).filter(
        MAImodel.status == 1,
        MAImodel.tenantid == tenant_id
    ).first()

    return model