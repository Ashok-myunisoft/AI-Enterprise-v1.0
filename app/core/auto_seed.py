import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

DEFAULT_MODEL_CODE = "gpt-4o"
DEFAULT_MODEL_NAME = "GPT-4o"


@dataclass(frozen=True)
class AgentSeed:
    initiative_code: str
    initiative_name: str
    capability_code: str
    capability_name: str
    bot_code: str
    bot_name: str
    bot_description: str
    prompt: str


AGENT_SEEDS = [
    AgentSeed(
        initiative_code="REPORT_ANALYZER",
        initiative_name="Report Analyzer",
        capability_code="ANALYZE_REPORT",
        capability_name="Analyze Report",
        bot_code="report_analyzer_bot",
        bot_name="Report Analyzer Bot",
        bot_description="AI Report Analyzer",
        prompt="Analyze the provided report input and return the result as structured JSON.",
    ),
    AgentSeed(
        initiative_code="REPORT_ANALYZER",
        initiative_name="Report Analyzer",
        capability_code="QUESTION_ANSWER",
        capability_name="Question Answer",
        bot_code="report_analyzer_bot",
        bot_name="Report Analyzer Bot",
        bot_description="AI Report Analyzer",
        prompt="Answer the user's question using the current report session context.",
    ),
    AgentSeed(
        initiative_code="EXTRACTOR_AGENT",
        initiative_name="Extractor Agent",
        capability_code="EXTRACT_DOCUMENT",
        capability_name="Extract Document",
        bot_code="extractor_bot",
        bot_name="Extractor Bot",
        bot_description="AI Document Extractor",
        prompt="Extract useful information from the uploaded document and return structured JSON.",
    ),
    AgentSeed(
        initiative_code="CREATOR_AGENT",
        initiative_name="Creator Agent",
        capability_code="GENERATE_VOUCHER",
        capability_name="Generate Voucher",
        bot_code="creator_bot",
        bot_name="Creator Bot",
        bot_description="AI Voucher Creator",
        prompt="Generate the requested voucher content from the user input.",
    ),
    AgentSeed(
        initiative_code="CHATBOT_AGENT",
        initiative_name="Chatbot Agent",
        capability_code="CHATBOT",
        capability_name="Chatbot",
        bot_code="chatbot_bot",
        bot_name="Chatbot Bot",
        bot_description="Enterprise Chatbot Agent",
        prompt="Respond to the user message as a helpful enterprise assistant.",
    ),
    AgentSeed(
        initiative_code="CHATINTERFACE_AGENT",
        initiative_name="Chat Interface Agent",
        capability_code="CHATINTERFACE",
        capability_name="Chat Interface",
        bot_code="chatinterface_bot",
        bot_name="Chat Interface Bot",
        bot_description="AI Chat Interface Agent",
        prompt="Respond to the user message through the chat interface.",
    ),
    AgentSeed(
        initiative_code="APPLICANT_AGENT",
        initiative_name="Applicant Agent",
        capability_code="APPLICANT_PROCESS",
        capability_name="Applicant Process",
        bot_code="applicant_bot",
        bot_name="Applicant Bot",
        bot_description="AI Applicant Agent",
        prompt="Process the applicant input and return the result as structured JSON.",
    ),
    AgentSeed(
        initiative_code="DOCUMENT_IDENTIFIER_AGENT",
        initiative_name="Document Identifier Agent",
        capability_code="IDENTIFY_DOCUMENT",
        capability_name="Identify Document",
        bot_code="document_identifier_bot",
        bot_name="Document Identifier Bot",
        bot_description="AI Document Identifier",
        prompt="Identify the uploaded document type and return the classification result as JSON.",
    ),
    AgentSeed(
        initiative_code="PARSE_VALIDATE_AGENT",
        initiative_name="Parse and Validate Agent",
        capability_code="PARSE_VALIDATE_DOCUMENT",
        capability_name="Parse and Validate Document",
        bot_code="parse_validate_bot",
        bot_name="Parse Validate Bot",
        bot_description="AI Parse and Validate Agent",
        prompt="Parse and validate the uploaded document and return the result as JSON.",
    ),
    AgentSeed(
        initiative_code="generate_profile",
        initiative_name="Generate Profile",
        capability_code="GENERATE_PROFILE",
        capability_name="Generate Job Profile",
        bot_code="generate_profile_bot",
        bot_name="Generate Profile Bot",
        bot_description="AI Job Profile Generator",
        prompt=(
            "You are an expert HR consultant and organizational psychologist. "
            "Generate a comprehensive, professional job profile based on the provided role information. "
            "Include: a detailed job description, measurable KPIs, a skills matrix (technical, soft, and domain), "
            "categorized interview questions (technical, managerial, situational), "
            "recommended psychometric assessment tools, and experience and qualification requirements. "
            "Return the result as structured JSON."
        ),
    ),
    AgentSeed(
        initiative_code="KMS_DISCOVERY_AGENT",
        initiative_name="KMS Discovery Agent",
        capability_code="KMS_EXTRACT",
        capability_name="KMS Extract",
        bot_code="kms_discovery_bot",
        bot_name="KMS Discovery Bot",
        bot_description="AI KMS Discovery Agent",
        prompt="Extract knowledge artifacts from the provided input and return structured candidates.",
    ),
]


def seed_agent(db: Session, tenant_id: int, seed: AgentSeed):
    from models.initiative import MAIinitiative
    from models.bot import MAIbot
    from models.capability import MAIcapability
    from models.prompt_template import MAIprompttemplate

    initiative = db.query(MAIinitiative).filter(
        MAIinitiative.aiinitiativecode == seed.initiative_code,
        MAIinitiative.tenantid == tenant_id,
    ).first()

    if not initiative:
        initiative = MAIinitiative(
            aiinitiativecode=seed.initiative_code,
            aiinitiativename=seed.initiative_name,
            maturitylevel=1,
            status=1,
            tenantid=tenant_id,
        )
        db.add(initiative)
        db.flush()
        logger.info("[auto_seed] Inserted initiative: %s", seed.initiative_code)

    capability = db.query(MAIcapability).filter(
        MAIcapability.AIcapabilitycode == seed.capability_code,
        MAIcapability.TENANTID == tenant_id,
    ).first()

    if not capability:
        capability = MAIcapability(
            AIcapabilitycode=seed.capability_code,
            AIcapabilityname=seed.capability_name,
            maxmaturitylevel=1,
            STATUS=1,
            TENANTID=tenant_id,
        )
        db.add(capability)
        db.flush()
        logger.info("[auto_seed] Inserted capability: %s", seed.capability_code)

    bot = db.query(MAIbot).filter(
        MAIbot.AIbotcode == seed.bot_code,
        MAIbot.TENANTID == tenant_id,
    ).first()

    if not bot:
        bot = MAIbot(
            AIbotcode=seed.bot_code,
            name=seed.bot_name,
            description=seed.bot_description,
            AIinitiativeid=initiative.aiinitiativeid,
            isreadonly=1,
            STATUS=1,
            VERSION=1,
            TENANTID=tenant_id,
        )
        db.add(bot)
        db.flush()
        logger.info("[auto_seed] Inserted bot: %s", seed.bot_code)

    prompt = db.query(MAIprompttemplate).filter(
        MAIprompttemplate.initiativecode == seed.initiative_code,
        MAIprompttemplate.capabilitycode == seed.capability_code,
        MAIprompttemplate.tenantid == tenant_id,
    ).first()

    if not prompt:
        prompt = MAIprompttemplate(
            initiativecode=seed.initiative_code,
            capabilitycode=seed.capability_code,
            tenantid=tenant_id,
            prompttemplate=seed.prompt,
            version=1,
            status=1,
        )
        db.add(prompt)
        db.flush()
        logger.info(
            "[auto_seed] Inserted prompt template: %s/%s",
            seed.initiative_code,
            seed.capability_code,
        )


def seed_default_model(db: Session, tenant_id: int):
    from models.model import MAImodel

    model = db.query(MAImodel).filter(
        MAImodel.tenantid == tenant_id,
        MAImodel.status == 1,
    ).first()

    if model:
        return

    model = MAImodel(
        modelcode=DEFAULT_MODEL_CODE,
        modelname=DEFAULT_MODEL_NAME,
        provider="openai",
        status=1,
        tenantid=tenant_id,
    )
    db.add(model)
    db.flush()
    logger.info("[auto_seed] Inserted model: %s", DEFAULT_MODEL_CODE)


def run_seeds(db: Session):
    tenant_id = 1
    try:
        for seed in AGENT_SEEDS:
            seed_agent(db, tenant_id, seed)
        seed_default_model(db, tenant_id)
        db.commit()
        logger.info("[auto_seed] Seed complete for tenant=%d", tenant_id)
    except Exception as e:
        db.rollback()
        logger.error("[auto_seed] Seed failed: %s", e, exc_info=True)
    finally:
        db.close()
