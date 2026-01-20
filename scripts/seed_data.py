import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, select
from app.db.session import AsyncSessionLocal, engine
from app.db.base_class import Base
# Ensure models are imported for Base.metadata to find them
from app.models import forms
from app.models.forms import Bank, FormTemplate

async def seed_data():
    print("🌱 Starting database seed...")
    
    # 0. Reset Schema for Forms (Fix for missing columns)
    try:
        async with engine.begin() as conn:
            print("⚠ Dropping old form tables...")
            await conn.execute(text("DROP TABLE IF EXISTS form_files CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS form_submissions CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS form_templates CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS banks CASCADE"))
            
            print("🏗 Recreating tables...")
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"Error resetting tables: {e}")
        return

    async with AsyncSessionLocal() as session:
        # 1. Create Banks
        banks_data = [
            {"name": "BDO Unibank", "code": "BDO", "description": "Banco de Oro - We Find Ways"},
            {"name": "Maya Bank", "code": "MAYA", "description": "Maya - It's everything and a bank"},
            {"name": "Security Bank", "code": "SECB", "description": "Security Bank - You deserve better"},
        ]
        
        created_banks = {}
        
        print("\n🏦 Creating Banks:")
        for data in banks_data:
            # Check if exists (should typically not exist after drop, but good practice)
            result = await session.execute(select(Bank).where(Bank.code == data["code"]))
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"   - {data['name']} (Already exists)")
                created_banks[data["code"]] = existing
            else:
                bank = Bank(**data)
                session.add(bank)
                await session.flush() # Flush to get ID
                print(f"   + {data['name']} (Created)")
                created_banks[data["code"]] = bank
        
        # 2. Create a Sample Form Template for BDO (Credit Card Application)
        if "BDO" in created_banks:
            bdo_bank = created_banks["BDO"]
            
            # JSONSchema for BDO Credit Card
            # Demonstrates: Validations, Conditional Logic (If/Else), File Uploads
            schema = {
                "type": "object",
                "title": "BDO Credit Card Application",
                "description": "Application form for Standard or Gold Javascript Mastercard",
                "properties": {
                    "applicant_info": {
                        "type": "object",
                        "title": "Applicant Information",
                        "properties": {
                            "first_name": {"type": "string", "minLength": 2, "title": "First Name"},
                            "last_name": {"type": "string", "minLength": 2, "title": "Last Name"},
                            "annual_income": {
                                "type": "number", 
                                "minimum": 150000, 
                                "title": "Annual Income (PHP)"
                            }
                        },
                        "required": ["first_name", "last_name", "annual_income"]
                    },
                    "card_type": {
                        "type": "string",
                        "title": "Card Type",
                        "enum": ["Standard", "Gold", "Platinum"],
                        "default": "Standard"
                    },
                    "existing_customer": {
                        "type": "boolean",
                        "title": "Are you an existing BDO customer?",
                        "default": False
                    },
                    "account_details": {
                        "type": "object",
                        "title": "Account Details",
                        "properties": {
                            "account_number": {
                                "type": "string",
                                "pattern": "^\\d{10,12}$",
                                "title": "Account Number",
                                "description": "10-12 digit account number"
                            }
                        },
                        "required": ["account_number"]
                    },
                    "documents": {
                        "type": "object",
                        "title": "Required Documents (File Uploads)",
                        "description": "Please upload securely locally. Tokens will be stored.",
                        "properties": {
                            "id_photo": {
                                "type": "string",
                                "format": "data-url", 
                                "title": "Upload Valid ID",
                                "description": "Stored as secure token"
                            },
                            "income_proof": {
                                "type": "string",
                                "title": "Proof of Income",
                                "description": "Stored as secure token"
                            }
                        }
                    }
                },
                "required": ["applicant_info", "card_type", "existing_customer"],
                # CONDITIONAL LOGIC using if/then
                "if": {
                    "properties": {
                        "existing_customer": {"const": True}
                    }
                },
                "then": {
                    "required": ["account_details"] # Require account number if existing customer
                }
            }
            
            ui_schema = {
                "ui:order": ["applicant_info", "existing_customer", "account_details", "card_type", "documents"]
            }
            
            # check if template exists
            result = await session.execute(
                select(FormTemplate).where(
                    FormTemplate.bank_id == bdo_bank.id,
                    FormTemplate.form_type == "credit_card"
                )
            )
            existing_template = result.scalar_one_or_none()
            
            print("\n📝 Creating Templates:")
            if existing_template:
                 print(f"   - BDO Credit Card Template (Already exists)")
            else:
                template = FormTemplate(
                    bank_id=bdo_bank.id,
                    form_type="credit_card",
                    version="1.0.0",
                    title="BDO Credit Card Application",
                    description="Apply for a new credit card",
                    json_schema=schema,
                    ui_schema=ui_schema,
                    is_active=True
                )
                session.add(template)
                print(f"   + BDO Credit Card Template (Created)")

        # 3. Maya Bank - Personal Loan Application
        # Demonstrates: Validations, Computed fields logic (via descriptions/UI)
        if "MAYA" in created_banks:
            maya_bank = created_banks["MAYA"]
            
            schema = {
                "type": "object",
                "title": "Maya Quick Loan",
                "description": "Get cash in minutes",
                "properties": {
                    "personal_info": {
                        "type": "object",
                        "title": "Who are you?",
                        "properties": {
                            "email": {"type": "string", "format": "email", "title": "Email Address"},
                            "mobile": {"type": "string", "pattern": "^09\\d{9}$", "title": "Mobile Number"}
                        },
                        "required": ["email", "mobile"]
                    },
                    "loan_details": {
                        "type": "object",
                        "title": "Loan Request",
                        "properties": {
                            "amount": {
                                "type": "integer",
                                "minimum": 5000,
                                "maximum": 50000,
                                "multipleOf": 1000,
                                "title": "Loan Amount (PHP)"
                            },
                            "terms": {
                                "type": "string",
                                "enum": ["1 Month", "3 Months", "6 Months"],
                                "title": "Payment Terms"
                            },
                            "purpose": {
                                "type": "string",
                                "title": "Purpose of Loan"
                            }
                        },
                        "required": ["amount", "terms"]
                    }
                },
                "required": ["personal_info", "loan_details"]
            }
            
            ui_schema = {"ui:order": ["personal_info", "loan_details"]}
            
            # Check exist
            result = await session.execute(select(FormTemplate).where(
                FormTemplate.bank_id == maya_bank.id,
                FormTemplate.form_type == "quick_loan"
            ))
            if not result.scalar_one_or_none():
                template = FormTemplate(
                    bank_id=maya_bank.id,
                    form_type="quick_loan",
                    version="1.0.0",
                    title="Maya Personal Loan",
                    description="Fast approval personal loan",
                    json_schema=schema,
                    ui_schema=ui_schema,
                    is_active=True
                )
                session.add(template)
                print(f"   + Maya Loan Template (Created)")

        # 4. Security Bank - KYC Form
        # Demonstrates: Nested objects, Arrays, Extensive data collection
        if "SECB" in created_banks:
            secb_bank = created_banks["SECB"]
            
            schema = {
                "type": "object",
                "title": "Security Bank KYC",
                "description": "Know Your Customer Form",
                "properties": {
                    "profile": {
                        "type": "object",
                        "title": "Client Profile",
                        "properties": {
                            "full_name": {"type": "string", "minLength": 5, "title": "Full Name"},
                            "birth_date": {"type": "string", "format": "date", "title": "Date of Birth"},
                            "nationality": {"type": "string", "title": "Nationality"},
                            "source_of_funds": {
                                "type": "array",
                                "title": "Source of Funds",
                                "items": {
                                    "type": "string",
                                    "enum": ["Salary", "Business", "Remittance", "Allowance", "Other"]
                                },
                                "minItems": 1,
                                "uniqueItems": True
                            }
                        },
                        "required": ["full_name", "birth_date", "source_of_funds"]
                    },
                    "address": {
                        "type": "object",
                        "title": "Address Information",
                        "properties": {
                            "street": {"type": "string", "title": "Street/Barangay"},
                            "city": {"type": "string", "title": "City/Municipality"},
                            "zip_code": {"type": "string", "pattern": "^\\d{4}$", "title": "Zip Code"}
                        },
                        "required": ["street", "city", "zip_code"]
                    },
                    "pep_declaration": {
                        "type": "boolean",
                        "title": "Are you a Politically Exposed Person (PEP)?",
                        "default": False
                    },
                    "pep_details": {
                        "type": "string",
                        "title": "Please specify position/relation"
                    }
                },
                "required": ["profile", "address", "pep_declaration"],
                "if": {
                    "properties": {"pep_declaration": {"const": True}}
                },
                "then": {
                    "required": ["pep_details"]
                }
            }
            
            ui_schema = {"ui:order": ["profile", "address", "pep_declaration", "pep_details"]}
            
            # Check exist
            result = await session.execute(select(FormTemplate).where(
                FormTemplate.bank_id == secb_bank.id,
                FormTemplate.form_type == "kyc_form"
            ))
            if not result.scalar_one_or_none():
                template = FormTemplate(
                    bank_id=secb_bank.id,
                    form_type="kyc_form",
                    version="1.0.0",
                    title="Security Bank High-Value KYC",
                    description="Standard KYC for high net worth individuals",
                    json_schema=schema,
                    ui_schema=ui_schema,
                    is_active=True
                )
                session.add(template)
                print(f"   + Security Bank KYC Template (Created)")

        await session.commit()
        print("\n✅ Seed completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
