"""
Run once to insert DB records required for the generate_profile service.
Usage (from project root):
    python seed_generate_profile.py
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL not set in .env")

TENANT_ID = 1   # change if your tenantId is different

engine = create_engine(DATABASE_URL)

PROMPT = (
    "You are an expert HR consultant and organizational psychologist. "
    "Generate a comprehensive, professional job profile based on the provided role information. "
    "Include: a detailed job description, measurable KPIs, a skills matrix (technical, soft, and domain), "
    "categorized interview questions (technical, managerial, situational), "
    "recommended psychometric assessment tools, and experience and qualification requirements. "
    "Return the result as structured JSON."
)

with engine.begin() as conn:

    # 1. Initiative
    conn.execute(text("""
        INSERT INTO maiinitiative (aiinitiativecode, aiinitiativename, maturitylevel, status, tenantid)
        VALUES ('generate_profile', 'Generate Profile', 1, 1, :tenant)
        ON CONFLICT (aiinitiativecode) DO NOTHING
    """), {"tenant": TENANT_ID})
    print("1. initiative  — OK")

    # 2. Capability
    conn.execute(text("""
        INSERT INTO maicapability (aicapabilitycode, aicapabilityname, maxmaturitylevel, status, tenantid)
        VALUES ('GENERATE_PROFILE', 'Generate Job Profile', 1, 1, :tenant)
        ON CONFLICT (aicapabilitycode) DO NOTHING
    """), {"tenant": TENANT_ID})
    print("2. capability  — OK")

    # 3. Bot (linked to the initiative; isreadonly=1 is required by the platform)
    conn.execute(text("""
        INSERT INTO maibot (aibotcode, name, description, aiinitiativeid, isreadonly, status, version, tenantid)
        SELECT
            'generate_profile_bot',
            'Generate Profile Bot',
            'AI Job Profile Generator',
            aiinitiativeid,
            1, 1, 1, :tenant
        FROM maiinitiative
        WHERE aiinitiativecode = 'generate_profile'
          AND tenantid = :tenant
        ON CONFLICT (aibotcode) DO NOTHING
    """), {"tenant": TENANT_ID})
    print("3. bot         — OK")

    # 4. Prompt template
    conn.execute(text("""
        INSERT INTO maiprompttemplate
            (initiativecode, capabilitycode, tenantid, prompttemplate, version, status)
        SELECT
            'generate_profile', 'GENERATE_PROFILE', :tenant, :prompt, 1, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM maiprompttemplate
            WHERE initiativecode = 'generate_profile'
              AND capabilitycode = 'GENERATE_PROFILE'
              AND tenantid = :tenant
        )
    """), {"tenant": TENANT_ID, "prompt": PROMPT})
    print("4. prompt      — OK")

    # 5. Model (only if no active model exists for this tenant yet)
    conn.execute(text("""
        INSERT INTO maimodel (modelcode, modelname, provider, status, tenantid)
        SELECT 'gpt-4o', 'GPT-4o', 'openai', 1, :tenant
        WHERE NOT EXISTS (
            SELECT 1 FROM maimodel WHERE tenantid = :tenant AND status = 1
        )
    """), {"tenant": TENANT_ID})
    print("5. model       — OK")

print("\nVerifying records...")
with engine.connect() as conn:
    init = conn.execute(text(
        "SELECT aiinitiativeid, aiinitiativecode FROM maiinitiative WHERE aiinitiativecode='generate_profile' AND tenantid=:t"
    ), {"t": TENANT_ID}).fetchone()

    bot = conn.execute(text(
        "SELECT aibotid, aibotcode FROM maibot WHERE aibotcode='generate_profile_bot' AND tenantid=:t"
    ), {"t": TENANT_ID}).fetchone()

    cap = conn.execute(text(
        "SELECT aicapabilityid, aicapabilitycode FROM maicapability WHERE aicapabilitycode='GENERATE_PROFILE' AND tenantid=:t"
    ), {"t": TENANT_ID}).fetchone()

    pt = conn.execute(text(
        "SELECT aipromptid FROM maiprompttemplate WHERE initiativecode='generate_profile' AND tenantid=:t"
    ), {"t": TENANT_ID}).fetchone()

    model = conn.execute(text(
        "SELECT aimodelid, modelcode FROM maimodel WHERE tenantid=:t AND status=1"
    ), {"t": TENANT_ID}).fetchone()

    print(f"  initiative : {dict(init._mapping) if init else 'MISSING'}")
    print(f"  bot        : {dict(bot._mapping) if bot else 'MISSING'}")
    print(f"  capability : {dict(cap._mapping) if cap else 'MISSING'}")
    print(f"  prompt     : {'found (id=' + str(pt[0]) + ')' if pt else 'MISSING'}")
    print(f"  model      : {dict(model._mapping) if model else 'MISSING'}")

    if all([init, bot, cap, pt, model]):
        print("\nAll records OK — generate_profile is ready to use.")
    else:
        print("\nWARNING: Some records are still missing. Check output above.")
