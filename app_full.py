from flask import Flask, render_template, request, jsonify, session
import random
import secrets
import json
import os
import math
from datetime import datetime, timedelta
from pathlib import Path
from flask import Blueprint

# Expose routes as a Blueprint so this module can be registered into the
# main application in `app_auth.py`.
bp = Blueprint('full', __name__)

ADVISOR_PROFILES = {
    'none': {
        'name': 'No Advisor',
        'description': 'No modifiers applied.'
    },
    'helper': {
        'name': 'Helper Advisor',
        'description': 'Provides guidance notifications only (no gameplay modifiers).'
    },
    'miranda': {
        'name': 'Miranda (Lawyer)',
        'description': 'Better legal protection, but slower growth/income.'
    },
    'gina': {
        'name': 'Gina (Hotel Owner)',
        'description': 'Business gains are stronger, stock trading is less effective.'
    },
    'katie': {
        'name': 'Katie (Hollywood Star)',
        'description': 'Lifestyle is more expensive.'
    },
    'rivera': {
        'name': 'Rivera (Criminal)',
        'description': 'Lower chance of getting caught in crime actions, but penalties are harsher when caught.'
    }
}

ILLEGAL_BUSINESS_TYPES = {
    'black_market': {
        'name': 'Black Market Stall',
        'startup_cost': 120000,
        'min_payout': 12000,
        'max_payout': 28000,
        'base_raid_chance': 0.20,
    },
    'counterfeit_lab': {
        'name': 'Counterfeit Lab',
        'startup_cost': 180000,
        'min_payout': 18000,
        'max_payout': 42000,
        'base_raid_chance': 0.24,
    },
}

# Comprehensive Illegal Business Categories (~70 Types)
# Criminal enterprises organized by operation type
ILLEGAL_BUSINESS_CATEGORIES = {
    'drug_production': {
        'name': 'Drug Production',
        'heat_multiplier': 1.5,  # Higher police attention
        'types': [
            'Meth Lab', 'Cocaine Processing Plant', 'Heroin Lab', 'Fentanyl Lab',
            'Cannabis Grow House', 'Hydroponic Farm', 'Synthetic Drug Lab',
            'Pill Mill Operation', 'Drug Compounding Lab'
        ],
        'typical_workers': (2, 50),
        'startup_cost_range': (50000, 2000000),
        'payout_multiplier': 1.8,
    },
    
    'drug_distribution': {
        'name': 'Drug Distribution',
        'heat_multiplier': 1.3,
        'types': [
            'Street Drug Network', 'Dark Web Drug Marketplace', 'Drug Trafficking Ring',
            'Pharmaceutical Diversion', 'Party Drug Distribution', 'Campus Drug Network',
            'Mobile Drug Delivery', 'Trap House'
        ],
        'typical_workers': (5, 200),
        'startup_cost_range': (30000, 500000),
        'payout_multiplier': 1.5,
    },
    
    'weapons_trafficking': {
        'name': 'Weapons & Arms Dealing',
        'heat_multiplier': 1.8,
        'types': [
            'Illegal Arms Dealer', 'Black Market Gun Shop', 'Weapons Smuggling Ring',
            'Military Arms Trafficking', 'Improvised Weapons Factory', 'Gun Modification Shop',
            'Explosives Manufacturing', 'Ammunition Black Market', 'Heavy Weapons Dealer'
        ],
        'typical_workers': (3, 100),
        'startup_cost_range': (100000, 5000000),
        'payout_multiplier': 2.0,
    },
    
    'cybercrime': {
        'name': 'Cybercrime & Hacking',
        'heat_multiplier': 1.0,  # Harder to detect
        'types': [
            'Ransomware Operation', 'Credit Card Fraud Ring', 'Identity Theft Network',
            'Crypto Hacking Collective', 'Phishing Operation', 'Data Breach Service',
            'DDoS-for-Hire', 'Botnet Operation', 'Cryptojacking Farm',
            'Dark Web Marketplace', 'Zero-Day Exploit Shop'
        ],
        'typical_workers': (1, 30),
        'startup_cost_range': (20000, 1000000),
        'payout_multiplier': 1.7,
    },
    
    'fraud_schemes': {
        'name': 'Fraud & Scams',
        'heat_multiplier': 1.1,
        'types': [
            'Ponzi Scheme', 'Pyramid Scheme', 'Investment Fraud Ring', 'Insurance Fraud Operation',
            'Medicare Fraud Network', 'Tax Fraud Service', 'Romance Scam Operation',
            'Telemarketing Scam Center', 'Fake Charity Scam', 'Bank Fraud Ring',
            'Mortgage Fraud Network'
        ],
        'typical_workers': (5, 100),
        'startup_cost_range': (40000, 800000),
        'payout_multiplier': 1.4,
    },
    
    'counterfeiting': {
        'name': 'Counterfeiting Operations',
        'heat_multiplier': 1.4,
        'types': [
            'Counterfeit Money Lab', 'Fake Document Service', 'Forged Passport Ring',
            'Counterfeit Goods Factory', 'Fake Designer Merchandise', 'Pirated Media Operation',
            'Fake Pharmaceutical Lab', 'Counterfeit Art Workshop', 'Fake ID Mill'
        ],
        'typical_workers': (2, 80),
        'startup_cost_range': (60000, 1500000),
        'payout_multiplier': 1.6,
    },
    
    'smuggling': {
        'name': 'Smuggling & Trafficking',
        'heat_multiplier': 1.9,  # Very high risk
        'types': [
            'Human Trafficking Ring', 'Exotic Animal Smuggling', 'Endangered Species Trade',
            'Contraband Cigarette Network', 'Art Smuggling Operation', 'Antiquities Trafficking',
            'Organ Trade Network', 'Rare Wood Smuggling', 'Diamond Smuggling Ring',
            'Cultural Artifact Theft'
        ],
        'typical_workers': (10, 500),
        'startup_cost_range': (200000, 10000000),
        'payout_multiplier': 2.5,
    },
    
    'illegal_gambling': {
        'name': 'Illegal Gambling',
        'heat_multiplier': 1.2,
        'types': [
            'Underground Casino', 'Illegal Betting Ring', 'Underground Fight Club',
            'Illegal Poker Room', 'Sports Betting Operation', 'Numbers Racket',
            'Shell Game Operation', 'Rigged Gambling Den', 'Illegal Horse Racing'
        ],
        'typical_workers': (5, 150),
        'startup_cost_range': (80000, 3000000),
        'payout_multiplier': 1.5,
    },
    
    'theft_fencing': {
        'name': 'Theft & Fencing',
        'heat_multiplier': 1.3,
        'types': [
            'Chop Shop', 'Stolen Goods Fence', 'Cargo Theft Ring', 'Retail Theft Network',
            'Jewelry Heist Operation', 'Art Theft Ring', 'Copper Theft Network',
            'Package Theft Organization', 'Warehouse Burglary Ring', 'Phone Theft Network'
        ],
        'typical_workers': (3, 100),
        'startup_cost_range': (30000, 1000000),
        'payout_multiplier': 1.4,
    },
    
    'vice_operations': {
        'name': 'Vice & Adult Services',
        'heat_multiplier': 1.1,
        'types': [
            'Underground Brothel', 'Escort Service Front', 'Illegal Strip Club',
            'Massage Parlor Front', 'Online Vice Network', 'Adult Content Piracy',
            'Illegal Cabaret'
        ],
        'typical_workers': (5, 80),
        'startup_cost_range': (50000, 800000),
        'payout_multiplier': 1.3,
    },
    
    'organized_crime': {
        'name': 'Organized Crime Rackets',
        'heat_multiplier': 1.6,
        'types': [
            'Protection Racket', 'Loan Sharking Operation', 'Extortion Ring',
            'Illegal Union Kickback Scheme', 'Construction Bid Rigging', 'Labor Racketeering',
            'Waste Management Racket', 'Port Control Operation', 'Political Bribery Network'
        ],
        'typical_workers': (10, 300),
        'startup_cost_range': (150000, 5000000),
        'payout_multiplier': 1.9,
    },
    
    'black_market_goods': {
        'name': 'Black Market Trading',
        'heat_multiplier': 1.2,
        'types': [
            'Illegal Pharmacy', 'Stolen Electronics Fence', 'Black Market Alcohol',
            'Untaxed Tobacco Network', 'Bootleg Merchandise', 'Grey Market Electronics',
            'Stolen Vehicle Parts', 'Black Market Luxury Goods', 'Contraband Food Trade'
        ],
        'typical_workers': (2, 60),
        'startup_cost_range': (40000, 600000),
        'payout_multiplier': 1.3,
    },
    
    'money_laundering': {
        'name': 'Money Laundering',
        'heat_multiplier': 1.4,
        'types': [
            'Front Company Laundry', 'Cash-Heavy Business Front', 'Shell Company Network',
            'Real Estate Flip Scheme', 'Art Gallery Money Wash', 'Casino Money Laundering',
            'Cryptocurrency Tumbling Service', 'Trade-Based Laundering'
        ],
        'typical_workers': (2, 40),
        'startup_cost_range': (100000, 3000000),
        'payout_multiplier': 1.2,  # Lower profit but essential
    },
    
    'environmental_crime': {
        'name': 'Environmental Crime',
        'heat_multiplier': 1.1,
        'types': [
            'Illegal Logging Operation', 'Toxic Waste Dumping', 'Illegal Mining',
            'Illegal Fishing Fleet', 'Wildlife Poaching Ring', 'Illegal Whaling',
            'E-Waste Dumping Network', 'Fracking Violation Operation'
        ],
        'typical_workers': (10, 200),
        'startup_cost_range': (100000, 2000000),
        'payout_multiplier': 1.4,
    },
    
    'corporate_crime': {
        'name': 'Corporate Crime',
        'heat_multiplier': 0.8,  # Often goes undetected
        'types': [
            'Insider Trading Ring', 'Stock Manipulation Scheme', 'Accounting Fraud',
            'Embezzlement Network', 'Corporate Espionage', 'Price Fixing Cartel',
            'Securities Fraud', 'Market Manipulation', 'Bribery Network'
        ],
        'typical_workers': (3, 50),
        'startup_cost_range': (200000, 10000000),
        'payout_multiplier': 2.2,
    },
}

# Illegal Business Size Classifications (Criminal Enterprise Tiers)
ILLEGAL_BUSINESS_SIZES = {
    'solo_operation': {
        'name': 'Solo Operation',
        'max_workers': 5,
        'max_partners': 0,
        'heat_reduction': 0,  # No heat benefit
        'territory_slots': 1,
    },
    'small_gang': {
        'name': 'Small Gang',
        'max_workers': 30,
        'max_partners': 2,
        'heat_reduction': 0.05,  # 5% less heat
        'territory_slots': 3,
    },
    'crime_syndicate': {
        'name': 'Crime Syndicate',
        'max_workers': 200,
        'max_partners': 5,
        'heat_reduction': 0.10,
        'territory_slots': 10,
    },
    'cartel': {
        'name': 'Cartel',
        'max_workers': 5000,
        'max_partners': 10,
        'heat_reduction': 0.15,  # Wealth and influence reduce heat
        'territory_slots': 50,
    }
}

# Criminal Worker Types (equivalent to regular employees)
CRIMINAL_WORKER_TYPES = {
    'enforcer': {
        'name': 'Enforcer',
        'cost': 3000,
        'daily_wage': 500,
        'heat_contribution': 0.02,  # Each adds 2% heat
        'revenue_contribution': 400,
    },
    'dealer': {
        'name': 'Dealer/Distributor',
        'cost': 2000,
        'daily_wage': 300,
        'heat_contribution': 0.03,
        'revenue_contribution': 600,
    },
    'smuggler': {
        'name': 'Smuggler',
        'cost': 5000,
        'daily_wage': 800,
        'heat_contribution': 0.04,
        'revenue_contribution': 1000,
    },
    'hacker': {
        'name': 'Hacker',
        'cost': 8000,
        'daily_wage': 1000,
        'heat_contribution': 0.01,  # Low heat (digital)
        'revenue_contribution': 1500,
    },
    'lookout': {
        'name': 'Lookout',
        'cost': 1000,
        'daily_wage': 200,
        'heat_contribution': -0.01,  # Reduces heat slightly
        'revenue_contribution': 100,
    },
    'money_mule': {
        'name': 'Money Mule',
        'cost': 2500,
        'daily_wage': 400,
        'heat_contribution': 0.015,
        'revenue_contribution': 300,
    },
}

# Comprehensive Business Industry Categories with 150+ Business Types
BUSINESS_INDUSTRIES = {
    'food_beverage': {
        'name': 'Food & Beverage',
        'business_type': 'Product',
        'types': [
            'Fast Food Chain', 'Fine Dining Restaurant', 'Coffee Shop', 'Food Truck', 
            'Catering Service', 'Bakery', 'Bar/Nightclub', 'Brewery/Distillery', 
            'Deli/Sandwich Shop', 'Pizza Restaurant', 'Sushi Restaurant', 'Steakhouse',
            'Vegan Restaurant', 'Ice Cream Parlor', 'Donut Shop', 'Juice Bar',
            'Food Processing Plant', 'Commercial Kitchen', 'Food Distributor'
        ],
        'typical_workers': (10, 500),
        'startup_cost_range': (50000, 2000000),
    },
    
    'retail_general': {
        'name': 'Retail - General',
        'business_type': 'Product',
        'types': [
            'Convenience Store', 'Supermarket', 'Department Store', 'Dollar Store',
            'Big-Box Retailer', 'Warehouse Club', 'Outlet Store', 'Pop-Up Shop',
            'Flea Market Stall', 'General Store'
        ],
        'typical_workers': (5, 5000),
        'startup_cost_range': (30000, 5000000),
    },
    
    'retail_specialty': {
        'name': 'Retail - Specialty',
        'business_type': 'Product',
        'types': [
            'Boutique Clothing Store', 'Shoe Store', 'Jewelry Store', 'Watch Shop',
            'Sporting Goods Store', 'Toy Store', 'Bookstore', 'Comic Shop',
            'Music Store', 'Art Supply Store', 'Craft Store', 'Pet Store',
            'Florist', 'Garden Center', 'Hardware Store', 'Home Goods Store'
        ],
        'typical_workers': (3, 200),
        'startup_cost_range': (40000, 800000),
    },
    
    'retail_electronics': {
        'name': 'Retail - Electronics & Tech',
        'business_type': 'Product',
        'types': [
            'Electronics Store', 'Computer Shop', 'Phone Store', 'Gaming Store',
            'Tech Accessory Shop', 'Camera Store', 'Audio Equipment Store',
            'Drone Store', 'Smart Home Store'
        ],
        'typical_workers': (5, 300),
        'startup_cost_range': (60000, 1500000),
    },
    
    'retail_automotive': {
        'name': 'Retail - Automotive',
        'business_type': 'Product',
        'types': [
            'Car Dealership', 'Used Car Lot', 'Motorcycle Dealership', 
            'RV Dealership', 'Boat Dealership', 'Auto Parts Store',
            'Tire Shop', 'Car Accessories Store'
        ],
        'typical_workers': (10, 500),
        'startup_cost_range': (100000, 5000000),
    },
    
    'retail_furniture': {
        'name': 'Retail - Home & Furniture',
        'business_type': 'Product',
        'types': [
            'Furniture Store', 'Mattress Store', 'Home Decor Shop', 
            'Lighting Store', 'Carpet/Flooring Store', 'Kitchen Store',
            'Bathroom Fixtures Store', 'Antique Shop'
        ],
        'typical_workers': (5, 250),
        'startup_cost_range': (50000, 1200000),
    },
    
    'professional_services': {
        'name': 'Professional Services',
        'business_type': 'Service',
        'types': [
            'Law Firm', 'Accounting Firm', 'Consulting Firm', 'Management Consulting',
            'HR Consulting', 'Tax Preparation Service', 'Financial Advisory',
            'Business Coaching', 'Career Counseling', 'Executive Search Firm',
            'Translation Services', 'Court Reporting', 'Notary Service'
        ],
        'typical_workers': (2, 500),
        'startup_cost_range': (20000, 1000000),
    },
    
    'marketing_advertising': {
        'name': 'Marketing & Advertising',
        'business_type': 'Service',
        'types': [
            'Advertising Agency', 'Marketing Agency', 'PR Firm', 'Social Media Agency',
            'SEO Agency', 'Content Marketing', 'Brand Consulting', 'Market Research Firm',
            'Media Buying Agency', 'Influencer Agency', 'Design Studio'
        ],
        'typical_workers': (5, 300),
        'startup_cost_range': (30000, 800000),
    },
    
    'finance_insurance': {
        'name': 'Finance & Insurance',
        'business_type': 'Service',
        'types': [
            'Investment Firm', 'Private Bank', 'Credit Union', 'Mortgage Company',
            'Insurance Agency', 'Life Insurance Provider', 'Property Insurance',
            'Investment Advisory', 'Wealth Management', 'Cryptocurrency Exchange',
            'Payment Processing', 'Crowdfunding Platform', 'Venture Capital Firm'
        ],
        'typical_workers': (10, 2000),
        'startup_cost_range': (100000, 10000000),
    },
    
    'healthcare_medical': {
        'name': 'Healthcare - Medical',
        'business_type': 'Service',
        'types': [
            'Medical Clinic', 'Dental Clinic', 'Urgent Care Center', 'Pediatric Clinic',
            'Dermatology Clinic', 'Eye Care Center', 'Physical Therapy Center',
            'Chiropractic Office', 'Mental Health Clinic', 'Substance Abuse Treatment',
            'Home Health Care', 'Medical Lab', 'Diagnostic Imaging Center'
        ],
        'typical_workers': (5, 500),
        'startup_cost_range': (150000, 3000000),
    },
    
    'healthcare_wellness': {
        'name': 'Healthcare - Wellness',
        'business_type': 'Service',
        'types': [
            'Pharmacy', 'Health Food Store', 'Vitamin Shop', 'Wellness Center',
            'Spa', 'Massage Therapy', 'Acupuncture Clinic', 'Yoga Studio',
            'Fitness Center', 'Gym', 'Personal Training', 'Meditation Center'
        ],
        'typical_workers': (3, 200),
        'startup_cost_range': (40000, 1000000),
    },
    
    'transportation_passenger': {
        'name': 'Transportation - Passenger',
        'business_type': 'Service',
        'types': [
            'Small Airline', 'Major Airline', 'Regional Airline', 'Charter Airline',
            'Taxi/Rideshare Company', 'Limousine Service', 'Bus Company',
            'Shuttle Service', 'Private Jet Service', 'Helicopter Tours'
        ],
        'typical_workers': (50, 50000),
        'startup_cost_range': (200000, 50000000),
    },
    
    'transportation_freight': {
        'name': 'Transportation - Freight & Logistics',
        'business_type': 'Service',
        'types': [
            'Freight/Logistics', 'Trucking Company', 'Moving Company',
            'Courier Service', 'Package Delivery', 'Warehouse Service',
            'Cold Storage Facility', 'Shipping Brokerage', 'Last-Mile Delivery'
        ],
        'typical_workers': (20, 10000),
        'startup_cost_range': (100000, 5000000),
    },
    
    'transportation_rental': {
        'name': 'Transportation - Rental',
        'business_type': 'Service',
        'types': [
            'Car Rental', 'Truck Rental', 'Bike Rental', 'Scooter Rental',
            'Boat Rental', 'RV Rental', 'Equipment Rental'
        ],
        'typical_workers': (5, 500),
        'startup_cost_range': (80000, 2000000),
    },
    
    'entertainment_venues': {
        'name': 'Entertainment - Venues',
        'business_type': 'Service',
        'types': [
            'Movie Theater', 'Concert Venue', 'Sports Arena', 'Comedy Club',
            'Theater/Playhouse', 'Drive-In Theater', 'Arcade', 'Bowling Alley',
            'Mini Golf Course', 'Go-Kart Track', 'Laser Tag Arena', 'Escape Room'
        ],
        'typical_workers': (10, 500),
        'startup_cost_range': (100000, 10000000),
    },
    
    'entertainment_media': {
        'name': 'Entertainment - Media & Production',
        'business_type': 'Service',
        'types': [
            'Film Production Company', 'Music Production Studio', 'Recording Studio',
            'Podcast Studio', 'Photography Studio', 'Video Production',
            'Animation Studio', 'Streaming Platform', 'Radio Station',
            'TV Network', 'YouTube Channel Business'
        ],
        'typical_workers': (5, 1000),
        'startup_cost_range': (50000, 5000000),
    },
    
    'entertainment_events': {
        'name': 'Entertainment - Events & Recreation',
        'business_type': 'Service',
        'types': [
            'Event Planning', 'Wedding Planning', 'Party Rental', 'DJ Service',
            'Catering Hall', 'Convention Center', 'Amusement Park', 'Water Park',
            'Zoo', 'Aquarium', 'Museum', 'Art Gallery'
        ],
        'typical_workers': (5, 2000),
        'startup_cost_range': (30000, 20000000),
    },
    
    'technology_software': {
        'name': 'Technology - Software & Development',
        'business_type': 'Service',
        'types': [
            'Software Company', 'SaaS Platform', 'Mobile App Developer',
            'Web Development Agency', 'Game Development Studio', 'AI/ML Company',
            'Cybersecurity Firm', 'Cloud Services', 'E-commerce Platform',
            'Fintech Startup', 'Edtech Platform'
        ],
        'typical_workers': (5, 5000),
        'startup_cost_range': (50000, 10000000),
    },
    
    'technology_hardware': {
        'name': 'Technology - Hardware & Infrastructure',
        'business_type': 'Product',
        'types': [
            'Data Center', 'Server Farm', 'Network Infrastructure',
            'Telecom Provider', 'Internet Service Provider', 'Hosting Provider',
            'IT Support Services', 'Computer Repair', 'Tech Consulting'
        ],
        'typical_workers': (10, 10000),
        'startup_cost_range': (100000, 50000000),
    },
    
    'manufacturing_automotive': {
        'name': 'Manufacturing - Automotive',
        'business_type': 'Product',
        'types': [
            'Car Manufacturing', 'Auto Parts Manufacturing', 'Tire Manufacturing',
            'Motorcycle Manufacturing', 'Bicycle Manufacturing', 'EV Manufacturing',
            'Aircraft Parts Manufacturing', 'Boat Manufacturing'
        ],
        'typical_workers': (500, 100000),
        'startup_cost_range': (5000000, 100000000),
    },
    
    'manufacturing_electronics': {
        'name': 'Manufacturing - Electronics',
        'business_type': 'Product',
        'types': [
            'Tech Hardware Manufacturing', 'Electronics Assembly', 'Chip Manufacturing',
            'Circuit Board Manufacturing', 'Battery Manufacturing', 'Display Manufacturing',
            'Consumer Electronics', 'Industrial Electronics'
        ],
        'typical_workers': (1000, 80000),
        'startup_cost_range': (10000000, 200000000),
    },
    
    'manufacturing_consumer_goods': {
        'name': 'Manufacturing - Consumer Goods',
        'business_type': 'Product',
        'types': [
            'Clothing Production', 'Textile Manufacturing', 'Footwear Manufacturing',
            'Toy Manufacturing', 'Furniture Manufacturing', 'Appliance Manufacturing',
            'Packaging Manufacturing', 'Plastic Products', 'Paper Products',
            'Printing Press'
        ],
        'typical_workers': (100, 10000),
        'startup_cost_range': (500000, 20000000),
    },
    
    'manufacturing_heavy_industry': {
        'name': 'Manufacturing - Heavy Industry',
        'business_type': 'Product',
        'types': [
            'Steel Mill', 'Metal Fabrication', 'Machinery Manufacturing',
            'Construction Equipment', 'Mining Equipment', 'Industrial Tools',
            'Chemical Plant', 'Refinery', 'Foundry'
        ],
        'typical_workers': (500, 20000),
        'startup_cost_range': (10000000, 500000000),
    },
    
    'real_estate': {
        'name': 'Real Estate',
        'business_type': 'Service',
        'types': [
            'Real Estate Agency', 'Property Management', 'Commercial Real Estate',
            'Real Estate Development', 'Real Estate Investment Trust', 'Title Company',
            'Appraisal Service', 'Home Inspection', 'Real Estate Staging'
        ],
        'typical_workers': (5, 500),
        'startup_cost_range': (30000, 10000000),
    },
    
    'construction': {
        'name': 'Construction',
        'business_type': 'Service',
        'types': [
            'General Contractor', 'Home Builder', 'Commercial Construction',
            'Remodeling Contractor', 'Roofing Company', 'Plumbing Company',
            'HVAC Company', 'Electrical Contractor', 'Landscaping Company',
            'Concrete Company', 'Demolition Company', 'Engineering Firm'
        ],
        'typical_workers': (10, 5000),
        'startup_cost_range': (50000, 5000000),
    },
    
    'education': {
        'name': 'Education & Training',
        'business_type': 'Service',
        'types': [
            'Private School', 'Tutoring Center', 'Test Prep Service', 'Language School',
            'Music School', 'Dance Studio', 'Art School', 'Coding Bootcamp',
            'Vocational Training', 'Driving School', 'Flight School', 'Online Course Platform'
        ],
        'typical_workers': (5, 1000),
        'startup_cost_range': (40000, 5000000),
    },
    
    'hospitality': {
        'name': 'Hospitality & Tourism',
        'business_type': 'Service',
        'types': [
            'Hotel', 'Motel', 'Boutique Hotel', 'Bed & Breakfast', 'Resort',
            'Hostel', 'Vacation Rental', 'Travel Agency', 'Tour Operator',
            'Cruise Line', 'Casino', 'Theme Restaurant'
        ],
        'typical_workers': (10, 5000),
        'startup_cost_range': (100000, 50000000),
    },
    
    'personal_services': {
        'name': 'Personal Services',
        'business_type': 'Service',
        'types': [
            'Hair Salon', 'Barber Shop', 'Nail Salon', 'Beauty Salon',
            'Day Spa', 'Tanning Salon', 'Tattoo Parlor', 'Dry Cleaning',
            'Laundromat', 'Tailoring Service', 'Shoe Repair', 'Watch Repair',
            'Locksmith', 'Cleaning Service', 'Pest Control', 'Security Service'
        ],
        'typical_workers': (2, 200),
        'startup_cost_range': (20000, 500000),
    },
    
    'agriculture': {
        'name': 'Agriculture & Farming',
        'business_type': 'Product',
        'types': [
            'Crop Farm', 'Dairy Farm', 'Cattle Ranch', 'Poultry Farm',
            'Vineyard/Winery', 'Orchard', 'Greenhouse/Nursery', 'Fish Farm',
            'Agricultural Supply', 'Farmers Market', 'Organic Farm'
        ],
        'typical_workers': (5, 5000),
        'startup_cost_range': (100000, 10000000),
    },
    
    'energy': {
        'name': 'Energy & Utilities',
        'business_type': 'Service',
        'types': [
            'Solar Farm', 'Wind Farm', 'Oil Company', 'Natural Gas Provider',
            'Electric Utility', 'Water Utility', 'Power Plant', 'Energy Consulting',
            'Gas Station', 'EV Charging Network'
        ],
        'typical_workers': (50, 10000),
        'startup_cost_range': (500000, 500000000),
    },
    
    'general': {
        'name': 'General Business',
        'business_type': 'Mixed',
        'types': ['General Business', 'Startup', 'Other'],
        'typical_workers': (1, 100),
        'startup_cost_range': (10000, 500000),
    }
}

# Business Size Classifications
BUSINESS_SIZES = {
    'solo': {
        'name': 'Solo Business',
        'max_employees': 5,
        'max_workers': 0,
        'max_partners': 0,
        'franchising_allowed': False,
    },
    'partnership': {
        'name': 'Partnership',
        'max_employees': 20,
        'max_workers': 50,
        'max_partners': 3,
        'franchising_allowed': False,
    },
    'major_service': {
        'name': 'Major Service',
        'max_employees': 100,
        'max_workers': 500,
        'max_partners': 5,
        'franchising_allowed': True,
    },
    'corporation': {
        'name': 'Corporation',
        'max_employees': 500,
        'max_workers': 100000,
        'max_partners': 10,
        'franchising_allowed': True,
    }
}

# Legal Business Structures
LEGAL_STRUCTURES = {
    'sole_proprietorship': {
        'name': 'Sole Proprietorship',
        'cost': 0,
        'tax_rate_modifier': 1.0,
        'liability_protection': False,
        'can_ipo': False,
        'description': 'Default structure. Personal assets at risk if business sued.'
    },
    'partnership': {
        'name': 'Partnership',
        'cost': 10000,
        'tax_rate_modifier': 1.0,
        'liability_protection': False,
        'can_ipo': False,
        'description': '2+ owners. Partners share liability.'
    },
    'llc': {
        'name': 'LLC (Limited Liability Company)',
        'cost': 50000,
        'tax_rate_modifier': 1.02,
        'liability_protection': True,
        'can_ipo': False,
        'description': 'Personal assets protected. Slightly higher tax rate.'
    },
    's_corp': {
        'name': 'S-Corporation',
        'cost': 150000,
        'tax_rate_modifier': 0.97,
        'liability_protection': True,
        'can_ipo': False,
        'annual_fee': 10000,
        'description': 'Lower tax rate but complex paperwork.'
    },
    'c_corp': {
        'name': 'C-Corporation',
        'cost': 500000,
        'tax_rate_modifier': 0.85,  # 15% fixed corporate rate
        'liability_protection': True,
        'can_ipo': True,
        'annual_fee': 25000,
        'description': 'Required for IPO. Heavy oversight, quarterly reports.'
    }
}

# Business Insurance Types
INSURANCE_TYPES = {
    'general_liability': {
        'name': 'General Liability Insurance',
        'cost': 5000,  # per month
        'coverage': 500000,
        'protects_against': ['lawsuits', 'damage_claims'],
    },
    'property': {
        'name': 'Property Insurance',
        'cost': 3000,
        'coverage': 1000000,
        'protects_against': ['fire', 'flood', 'robbery'],
    },
    'revenue_loss': {
        'name': 'Revenue Loss Insurance',
        'cost': 10000,
        'coverage': 100000,
        'protects_against': ['shutdown', 'strike', 'pandemic'],
    },
    'full_coverage': {
        'name': 'Full Coverage (All-in-One)',
        'cost': 15000,
        'coverage': 2000000,
        'protects_against': ['all'],
        'bonus': 0.05,  # +5% customer confidence
    }
}

# Business Loan Types
BUSINESS_LOAN_TYPES = {
    'startup': {
        'name': 'Startup Loan',
        'max_amount': 200000,
        'interest_rate': 0.08,
        'term_days': 30,
        'requirements': {'min_age_days': 0}
    },
    'expansion': {
        'name': 'Expansion Loan',
        'max_amount': 2000000,
        'interest_rate': 0.10,
        'term_days': 60,
        'requirements': {'min_age_days': 7, 'positive_cash_flow': True}
    },
    'acquisition': {
        'name': 'Acquisition Loan',
        'max_amount': 10000000,
        'interest_rate': 0.12,
        'term_days': 90,
        'requirements': {'min_age_days': 14, 'positive_cash_flow': True}
    },
    'emergency': {
        'name': 'Emergency Bridge Loan',
        'max_amount': 500000,
        'interest_rate': 0.15,
        'term_days': 7,
        'requirements': {'min_age_days': 3}
    }
}

# Data directories
DATA_DIR = Path('game_data')
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / 'users.json'
BUSINESSES_FILE = DATA_DIR / 'businesses.json'
CONFIG_FILE = DATA_DIR / 'config.json'
STOCKS_FILE = DATA_DIR / 'stocks.json'
CRYPTO_FILE = DATA_DIR / 'crypto.json'
SHOP_FILE = DATA_DIR / 'shop.json'
FEEDBACK_FILE = DATA_DIR / 'feedback.json'
HOURLY_LOG_FILE = DATA_DIR / 'hourly_log.json'
ERROR_LOGS_FILE = DATA_DIR / 'error_logs.json'

# ==================== DATA LOADING/SAVING ====================

def load_json(file, default):
    if file.exists():
        try:
            with open(file, 'r') as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(file, data):
    # Ensure parent directory exists
    file.parent.mkdir(parents=True, exist_ok=True)
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

def load_users():
    return load_json(USERS_FILE, {})

def save_users(data):
    save_json(USERS_FILE, data)

def load_businesses():
    return load_json(BUSINESSES_FILE, {})

def save_businesses(data):
    save_json(BUSINESSES_FILE, data)

def load_config():
    defaults = {
        'emergencyCap': 250000,
        'taxRate': 0.1,
        'highIncomeRate': 0.25,
        'inflation': 0.02,
        'govTaxPercent': 21,
        'govShutdown': False,
        'recession': False,
        'depression': False,
        'interestRate': 3,
        'baseInterestRate': 3,
        'centralBankVault': 1000000,
        'businessTaxPool': 0,
        'savingsInterestPool': 0,
        'infrastructureMaintenancePool': 0,
        'lastHourlyUpdate': None,
        'strikeMode': False
    }
    data = load_json(CONFIG_FILE, defaults)
    for k, v in defaults.items():
        if k not in data:
            data[k] = v
    return data

def save_config(data):
    save_json(CONFIG_FILE, data)

def load_stocks():
    defaults = {
        # S&P12 - Major AI Businesses (Index Components)
        'APEX': {'name': 'Apex Technologies', 'price': 250, 'history': [], 'shares': 1000000, 'type': 'ai_business', 'sp12': True, 'change_points': 0},
        'NOVA': {'name': 'Nova Financial Group', 'price': 180, 'history': [], 'shares': 2000000, 'type': 'ai_business', 'sp12': True, 'change_points': 0},
        'TITAN': {'name': 'Titan Manufacturing', 'price': 320, 'history': [], 'shares': 800000, 'type': 'ai_business', 'sp12': True, 'change_points': 0},
        'PULSE': {'name': 'Pulse HealthCare', 'price': 420, 'history': [], 'shares': 500000, 'type': 'ai_business', 'sp12': True, 'change_points': 0},
        'ZENITH': {'name': 'Zenith Energy Corp', 'price': 290, 'history': [], 'shares': 1200000, 'type': 'ai_business', 'sp12': True, 'change_points': 0},
        'VERTEX': {'name': 'Vertex Retail Chain', 'price': 150, 'history': [], 'shares': 3000000, 'type': 'ai_business', 'sp12': True, 'change_points': 0},
        'QUANTUM': {'name': 'Quantum Computing Inc', 'price': 580, 'history': [], 'shares': 400000, 'type': 'ai_business', 'sp12': True, 'change_points': 0},
        'ATLAS': {'name': 'Atlas Logistics', 'price': 210, 'history': [], 'shares': 1500000, 'type': 'ai_business', 'sp12': True, 'change_points': 0},
        'NEXUS': {'name': 'Nexus Media Group', 'price': 175, 'history': [], 'shares': 2500000, 'type': 'ai_business', 'sp12': True, 'change_points': 0},
        'STELLAR': {'name': 'Stellar Aerospace', 'price': 640, 'history': [], 'shares': 300000, 'type': 'ai_business', 'sp12': True, 'change_points': 0},
        'FUSION': {'name': 'Fusion Pharmaceuticals', 'price': 380, 'history': [], 'shares': 700000, 'type': 'ai_business', 'sp12': True, 'change_points': 0},
        'HORIZON': {'name': 'Horizon Real Estate', 'price': 260, 'history': [], 'shares': 1100000, 'type': 'ai_business', 'sp12': True, 'change_points': 0},
        
        # Additional AI Businesses (Not in S&P12)
        'SPARK': {'name': 'Spark Gaming Studios', 'price': 95, 'history': [], 'shares': 4000000, 'type': 'ai_business', 'sp12': False, 'change_points': 0},
        'WAVE': {'name': 'Wave Telecommunications', 'price': 130, 'history': [], 'shares': 2800000, 'type': 'ai_business', 'sp12': False, 'change_points': 0},
        'ECHO': {'name': 'Echo E-Commerce', 'price': 88, 'history': [], 'shares': 5000000, 'type': 'ai_business', 'sp12': False, 'change_points': 0},
        'PRIME': {'name': 'Prime Automotive', 'price': 220, 'history': [], 'shares': 1800000, 'type': 'ai_business', 'sp12': False, 'change_points': 0},
        'OLYMPUS': {'name': 'Olympus Hotels', 'price': 165, 'history': [], 'shares': 2200000, 'type': 'ai_business', 'sp12': False, 'change_points': 0},
        'PHOENIX': {'name': 'Phoenix Biotech', 'price': 445, 'history': [], 'shares': 600000, 'type': 'ai_business', 'sp12': False, 'change_points': 0},
        'SUMMIT': {'name': 'Summit Insurance', 'price': 195, 'history': [], 'shares': 2000000, 'type': 'ai_business', 'sp12': False, 'change_points': 0},
        'VELOCITY': {'name': 'Velocity Delivery', 'price': 72, 'history': [], 'shares': 6000000, 'type': 'ai_business', 'sp12': False, 'change_points': 0},
    }
    return load_json(STOCKS_FILE, defaults)

def save_stocks(data):
    save_json(STOCKS_FILE, data)

def load_crypto():
    defaults = {
        'BTC': {'name': 'Bitcoin', 'price': 50000, 'history': []},
        'ETH': {'name': 'Ethereum', 'price': 3000, 'history': []},
        'DOGE': {'name': 'Dogecoin', 'price': 0.25, 'history': []},
    }
    return load_json(CRYPTO_FILE, defaults)

def save_crypto(data):
    save_json(CRYPTO_FILE, data)

def load_shop():
    defaults = {
        # Housing
        'apartment': {'name': 'Apartment', 'price': 50000, 'maxOwn': 1, 'rentHourly': 550, 'type': 'housing', 'category': 'housing'},
        'house': {'name': 'House', 'price': 150000, 'maxOwn': 8, 'rentDaily': 2500, 'type': 'housing', 'category': 'housing'},
        'mansion': {'name': 'Mansion', 'price': 500000, 'maxOwn': 3, 'rentDaily': 25000, 'type': 'housing', 'category': 'housing'},
        
        # Basic Collectibles
        'cookie': {'name': 'Cookie', 'price': 2, 'maxOwn': float('inf'), 'type': 'collectible', 'category': 'collectible'},
        'pinkfeet': {'name': 'Pink Feet', 'price': 8, 'maxOwn': float('inf'), 'type': 'collectible', 'category': 'collectible'},
        'feetpic': {'name': 'Feet Pic', 'price': 5, 'maxOwn': float('inf'), 'type': 'collectible', 'category': 'collectible'},
        'jar': {'name': 'Jar', 'price': 3, 'maxOwn': float('inf'), 'type': 'collectible', 'category': 'collectible'},
        'animefigurine': {'name': 'Anime Figurine', 'price': 30, 'maxOwn': float('inf'), 'type': 'collectible', 'category': 'collectible'},
        
        # Precious Metals & Rare Collectibles
        'goldbar': {'name': 'Gold Bar (1oz)', 'price': 2000, 'maxOwn': float('inf'), 'type': 'collectible', 'category': 'collectible', 'resellValue': 1900},
        'silverbar': {'name': 'Silver Bar (10oz)', 'price': 240, 'maxOwn': float('inf'), 'type': 'collectible', 'category': 'collectible', 'resellValue': 230},
        'platinum': {'name': 'Platinum Coin', 'price': 1100, 'maxOwn': float('inf'), 'type': 'collectible', 'category': 'collectible', 'resellValue': 1050},
        'diamond': {'name': 'Diamond (1 carat)', 'price': 5000, 'maxOwn': float('inf'), 'type': 'collectible', 'category': 'collectible', 'resellValue': 4500},
        'ruby': {'name': 'Ruby Gemstone', 'price': 2500, 'maxOwn': float('inf'), 'type': 'collectible', 'category': 'collectible', 'resellValue': 2200},
        'emerald': {'name': 'Emerald Gemstone', 'price': 3000, 'maxOwn': float('inf'), 'type': 'collectible', 'category': 'collectible', 'resellValue': 2700},
        'rolex': {'name': 'Luxury Watch', 'price': 15000, 'maxOwn': float('inf'), 'type': 'collectible', 'category': 'collectible', 'resellValue': 13000},
        'painting': {'name': 'Fine Art Painting', 'price': 8000, 'maxOwn': float('inf'), 'type': 'collectible', 'category': 'collectible', 'resellValue': 7000},
        
        # Small Cars
        'toyoda_coralla': {'name': 'Toyoda Coralla', 'price': 22000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'small'},
        'handa_civic': {'name': 'Handa Civic', 'price': 24000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'small'},
        'fard_fiesta': {'name': 'Fard Fiesta', 'price': 18000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'small'},
        'chevralet_spark': {'name': 'Chevralet Spark', 'price': 15000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'small'},
        
        # Sedans
        'fard_fusion': {'name': 'Fard Fusion', 'price': 28000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'sedan'},
        'toyoda_camree': {'name': 'Toyoda Camree', 'price': 26000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'sedan'},
        'handa_accord': {'name': 'Handa Accord', 'price': 27000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'sedan'},
        'nissin_altima': {'name': 'Nissin Altima', 'price': 25000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'sedan'},
        'hyunduh_sonata': {'name': 'Hyunduh Sonata', 'price': 26000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'sedan'},
        
        # SUVs
        'fard_explorer': {'name': 'Fard Explorer', 'price': 38000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'suv'},
        'chevralet_tahoe': {'name': 'Chevralet Tahoe', 'price': 52000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'suv'},
        'toyoda_highlander': {'name': 'Toyoda Highlander', 'price': 40000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'suv'},
        'handa_pilot': {'name': 'Handa Pilot', 'price': 39000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'suv'},
        
        # Mid-Sized SUVs
        'fard_escape': {'name': 'Fard Escape', 'price': 30000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'mid_suv'},
        'toyoda_rav4': {'name': 'Toyoda RAV4', 'price': 29000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'mid_suv'},
        'handa_crv': {'name': 'Handa CR-V', 'price': 31000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'mid_suv'},
        'nissin_rogue': {'name': 'Nissin Rogue', 'price': 28000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'mid_suv'},
        
        # Electric Cars
        'tosla_model3': {'name': 'Tosla Model 3', 'price': 42000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'electric'},
        'tosla_modely': {'name': 'Tosla Model Y', 'price': 52000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'electric'},
        'chevralet_volt': {'name': 'Chevralet Volt', 'price': 34000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'electric'},
        'fard_mustang_e': {'name': 'Fard Mustang-E', 'price': 48000, 'maxOwn': 5, 'type': 'vehicle', 'category': 'vehicle', 'class': 'electric'},
        
        # Luxury Cars
        'linkkon_navigator': {'name': 'Linkkon Navigator', 'price': 85000, 'maxOwn': 3, 'type': 'vehicle', 'category': 'vehicle', 'class': 'luxury'},
        'cadilac_escalade': {'name': 'Cadilac Escalade', 'price': 80000, 'maxOwn': 3, 'type': 'vehicle', 'category': 'vehicle', 'class': 'luxury'},
        'bmv_7series': {'name': 'BMV 7 Series', 'price': 95000, 'maxOwn': 3, 'type': 'vehicle', 'category': 'vehicle', 'class': 'luxury'},
        'mercades_sclass': {'name': 'Mercades S-Class', 'price': 110000, 'maxOwn': 3, 'type': 'vehicle', 'category': 'vehicle', 'class': 'luxury'},
        'audi_a8': {'name': 'Audi A8', 'price': 90000, 'maxOwn': 3, 'type': 'vehicle', 'category': 'vehicle', 'class': 'luxury'},
        'lexas_ls': {'name': 'Lexas LS', 'price': 78000, 'maxOwn': 3, 'type': 'vehicle', 'category': 'vehicle', 'class': 'luxury'},
        
        # Sports Cars
        'fard_mustang': {'name': 'Fard Mustang', 'price': 45000, 'maxOwn': 3, 'type': 'vehicle', 'category': 'vehicle', 'class': 'sports'},
        'chevralet_corvette': {'name': 'Chevralet Corvette', 'price': 68000, 'maxOwn': 3, 'type': 'vehicle', 'category': 'vehicle', 'class': 'sports'},
        'dodge_challenger': {'name': 'Dodge Challenger', 'price': 50000, 'maxOwn': 3, 'type': 'vehicle', 'category': 'vehicle', 'class': 'sports'},
        'porsh_911': {'name': 'Porsh 911', 'price': 120000, 'maxOwn': 2, 'type': 'vehicle', 'category': 'vehicle', 'class': 'sports'},
        'nissen_gtr': {'name': 'Nissen GT-R', 'price': 115000, 'maxOwn': 2, 'type': 'vehicle', 'category': 'vehicle', 'class': 'sports'},
        'bmv_m3': {'name': 'BMV M3', 'price': 72000, 'maxOwn': 3, 'type': 'vehicle', 'category': 'vehicle', 'class': 'sports'},
        'audi_r8': {'name': 'Audi R8', 'price': 150000, 'maxOwn': 2, 'type': 'vehicle', 'category': 'vehicle', 'class': 'sports'},
        'lamborguini_huracan': {'name': 'Lamborguini Huracan', 'price': 250000, 'maxOwn': 1, 'type': 'vehicle', 'category': 'vehicle', 'class': 'sports'},
        'ferari_488': {'name': 'Ferari 488', 'price': 280000, 'maxOwn': 1, 'type': 'vehicle', 'category': 'vehicle', 'class': 'sports'},
        
        # Mystery Boxes
        'mystery_box_t3': {'name': 'Mystery Box (Tier 3)', 'price': 200, 'maxOwn': float('inf'), 'type': 'mystery_box', 'category': 'mystery_box', 'tier': 3},
        'mystery_box_t2': {'name': 'Mystery Box (Tier 2)', 'price': 2000, 'maxOwn': float('inf'), 'type': 'mystery_box', 'category': 'mystery_box', 'tier': 2},
        'mystery_box_t1': {'name': 'Mystery Box (Tier 1)', 'price': 25000, 'maxOwn': float('inf'), 'type': 'mystery_box', 'category': 'mystery_box', 'tier': 1},
    }
    return load_json(SHOP_FILE, defaults)


def _coerce_int_amount(value) -> int:
    try:
        if value is None:
            return 0
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            if math.isnan(value) or math.isinf(value):
                return 0
            return int(value)
        text = str(value).strip()
        if not text:
            return 0
        return int(float(text))
    except Exception:
        return 0


def compute_central_bank_vault(users=None) -> int:
    """Central bank vault = sum of all user checking + savings (deposits)."""
    users = users if isinstance(users, dict) else load_users()
    total = 0
    for _, user in users.items():
        if not isinstance(user, dict):
            continue
        total += _coerce_int_amount(user.get('checking', 0))
        total += _coerce_int_amount(user.get('savings', 0))
    return max(0, int(total))


def load_hourly_log() -> list:
    data = load_json(HOURLY_LOG_FILE, [])
    if isinstance(data, dict) and isinstance(data.get('entries'), list):
        data = data.get('entries', [])
    if not isinstance(data, list):
        return []
    # keep only well-formed dict entries
    return [e for e in data if isinstance(e, dict)]


def append_hourly_log(entry: dict) -> None:
    if not isinstance(entry, dict):
        return
    entries = load_hourly_log()
    entries.append(entry)
    entries = entries[-200:]
    save_json(HOURLY_LOG_FILE, entries)

def load_error_logs() -> list:
    """Load error logs from file."""
    data = load_json(ERROR_LOGS_FILE, [])
    if not isinstance(data, list):
        return []
    return [e for e in data if isinstance(e, dict)]

def save_error_logs(errors: list) -> None:
    """Save error logs to file."""
    save_json(ERROR_LOGS_FILE, errors)

def append_error_log(error: dict) -> None:
    """Append a new error to the log, keeping last 500 entries."""
    if not isinstance(error, dict):
        return
    errors = load_error_logs()
    error['timestamp'] = datetime.now().isoformat()
    errors.append(error)
    # Keep last 500 errors
    save_error_logs(errors[-500:])

# ==================== WORK MESSAGES ====================

WORK_MESSAGES = [
    "You fixed some fences and made ${amount}",
    "You mowed lawns all day and earned ${amount}",
    "You helped move furniture and made ${amount}",
    "You washed cars and brought home ${amount}",
    "You did some freelance work and earned ${amount}",
    "You sold handmade crafts and made ${amount}",
    "You delivered packages and earned ${amount}",
    "You walked dogs around the neighborhood and made ${amount}",
    "You cleaned houses and earned ${amount}",
    "You did yard work and brought home ${amount}",
]

GOV_MESSAGES = [
    "You worked for the TSA screening luggage",
    "You filed paperwork at the DMV",
    "You inspected buildings for the city",
    "You worked as a postal worker",
    "You processed permits at City Hall",
    "You worked road maintenance for the state",
    "You worked at the Department of Education",
    "You assisted at the Department of Defense",
    "You helped at the Department of Health",
]

SHUTDOWN_MESSAGES = [
    "You showed up to work at the TSA, but the government is shut down. You got nothing!",
    "You tried to work at the DMV but it's closed due to government shutdown. $0 earned.",
    "Government shutdown! Your shift was cancelled. No pay today!",
]

ROB_SUCCESS_MESSAGES = [
    "You snuck into their house and stole ${amount}!",
    "You picked their pocket and got away with ${amount}!",
    "You hacked their account and transferred ${amount}!",
    "You found their wallet and took ${amount}!",
]

ROB_FAIL_MESSAGES = [
    "You got caught! The police arrested you.",
    "Security cameras spotted you! You're going to jail.",
    "They caught you red-handed! Off to jail you go.",
    "The alarm went off! Police got you.",
]

# ==================== UTILITY FUNCTIONS ====================

def generate_unique_friend_code(users: dict) -> str:
    existing = {
        str(u.get('friend_code'))
        for u in users.values()
        if u.get('friend_code') is not None and str(u.get('friend_code')).strip()
    }

    for _ in range(100):
        code = str(secrets.randbelow(900000) + 100000)
        if code not in existing:
            return code

    # Fallback: keep bumping until unique.
    code_int = secrets.randbelow(900000) + 100000
    while str(code_int) in existing:
        code_int = (code_int % 900000) + 100000
    return str(code_int)


def resolve_user_identifier(users: dict, identifier: str):
    """Resolve a username or 6-digit friend code to a users.json key."""
    if not identifier:
        return None

    raw = identifier.strip()
    if not raw:
        return None

    if raw.isdigit() and len(raw) == 6:
        for uid, u in users.items():
            if str(u.get('friend_code', '')).strip() == raw:
                return uid
        return None

    key = raw.lower()
    if key in users:
        return key
    return None

def ensure_user(user_id):
    users = load_users()
    changed = False
    if user_id not in users:
        users[user_id] = {
            'createdAccount': False,
            'accountType': None,
            'hasCheckingAccount': False,
            'hasSavingsAccount': False,
            'checking': 0,
            'savings': 0,
            'pockets': 0,
            'emergency': 0,
            'businesses': [],
            'stocks': {},
            'crypto': {},
            'inventory': {},
            'loans': {
                'regular': {'principal': 0, 'spent': 0, 'currentDebt': 0, 'missedDays': 0, 'inCollections': False, 'startDate': None},
                'stock': {'principal': 0, 'spent': 0, 'currentDebt': 0, 'inCollections': False, 'startDate': None}
            },
            'cooldowns': {},
            'arrests': 0,
            'hasInsurance': False,
            'totalRobbedFrom': 0,
            'totalRobbedOthers': 0,
            'lastWorkDay': None,
            'illegalBusinesses': [],
            'advisor': 'none',
            'notifications': [],
            'nextNotificationId': 1,
            'friends': [],
            'friendRequests': [],
            'achievements': {
                'unlocked': [],
                'stats': {}
            },
            'casino_stats': {
                'slots_played': 0,
                'slots_wagered': 0,
                'slots_won': 0,
                'biggest_slots_win': 0,
                'blackjack_played': 0,
                'blackjack_wagered': 0,
                'blackjack_won': 0
            },
            'trade_history': [],
            # NEW: Login & Activity Tracking
            'lastLogin': None,
            'lastLoginBonus': None,
            'loginStreak': 0,
            'totalLogins': 0,
            # NEW: Work Streak
            'workStreak': 0,
            'lastWorkDate': None,
            # NEW: Transaction History
            'transactions': [],
            # NEW: Profile Stats
            'totalEarned': 0,
            'totalSpent': 0,
            'totalWorked': 0,
            'accountCreatedAt': datetime.now().isoformat()
        }
        changed = True
    
    user = users[user_id]
    if 'advisor' not in user:
        user['advisor'] = 'none'
        changed = True
    if 'notifications' not in user:
        user['notifications'] = []
        changed = True
    if 'nextNotificationId' not in user:
        user['nextNotificationId'] = 1
        changed = True
    if 'illegalBusinesses' not in user:
        user['illegalBusinesses'] = []
        changed = True
    if 'friends' not in user:
        user['friends'] = []
        changed = True
    if 'friendRequests' not in user:
        user['friendRequests'] = []
        changed = True
    if 'achievements' not in user:
        user['achievements'] = {
            'unlocked': [],
            'stats': {}
        }
        changed = True
    if 'casino_stats' not in user:
        user['casino_stats'] = {
            'slots_played': 0,
            'slots_wagered': 0,
            'slots_won': 0,
            'biggest_slots_win': 0,
            'blackjack_played': 0,
            'blackjack_wagered': 0,
            'blackjack_won': 0
        }
        changed = True
    if 'trade_history' not in user:
        user['trade_history'] = []
        changed = True
    # NEW: Bank account tracking
    if 'hasCheckingAccount' not in user:
        user['hasCheckingAccount'] = user.get('createdAccount', False)
        changed = True
    if 'hasSavingsAccount' not in user:
        user['hasSavingsAccount'] = user.get('createdAccount', False)
        changed = True
    # NEW: Login & Activity Tracking
    if 'lastLogin' not in user:
        user['lastLogin'] = None
        changed = True
    if 'lastLoginBonus' not in user:
        user['lastLoginBonus'] = None
        changed = True
    if 'loginStreak' not in user:
        user['loginStreak'] = 0
        changed = True
    if 'totalLogins' not in user:
        user['totalLogins'] = 0
        changed = True
    # NEW: Work Streak
    if 'workStreak' not in user:
        user['workStreak'] = 0
        changed = True
    if 'lastWorkDate' not in user:
        user['lastWorkDate'] = None
        changed = True
    # NEW: Transaction History
    if 'transactions' not in user:
        user['transactions'] = []
        changed = True
    # NEW: Profile Stats
    if 'totalEarned' not in user:
        user['totalEarned'] = 0
        changed = True
    if 'totalSpent' not in user:
        user['totalSpent'] = 0
        changed = True
    if 'totalWorked' not in user:
        user['totalWorked'] = 0
        changed = True
    if 'accountCreatedAt' not in user:
        user['accountCreatedAt'] = datetime.now().isoformat()
        changed = True

    if 'friend_code' not in user or not str(user.get('friend_code') or '').strip():
        user['friend_code'] = generate_unique_friend_code(users)
        changed = True

    if changed and len(user.get('notifications', [])) == 0:
        add_notification(
            user,
            '👋 Welcome to EconGame beta! Thanks for playing — your data is saved locally for testing.',
            'info'
        )

    if changed:
        save_users(users)
    return users[user_id]

def ensure_runtime_fields(user):
    if 'advisor' not in user:
        user['advisor'] = 'none'
    if 'notifications' not in user:
        user['notifications'] = []
    if 'nextNotificationId' not in user:
        user['nextNotificationId'] = 1
    if 'illegalBusinesses' not in user:
        user['illegalBusinesses'] = []

def add_notification(user, message, level='info'):
    ensure_runtime_fields(user)
    notification = {
        'id': user['nextNotificationId'],
        'message': message,
        'level': level,
        'read': False,
        'createdAt': datetime.now().isoformat()
    }
    user['nextNotificationId'] += 1
    user['notifications'].append(notification)
    user['notifications'] = user['notifications'][-100:]

def maybe_add_helper_notifications(user):
    ensure_runtime_fields(user)
    advisor = user.get('advisor', 'none')
    if advisor not in ['helper', 'none']:
        return

    # Helper function to check if unread notification with same message exists
    def has_unread_notification(message):
        return any(
            n.get('message') == message and not n.get('read', False)
            for n in user.get('notifications', [])
        )

    pockets = user.get('pockets', 0)
    pockets_msg = '💡 Helper: Your pockets are low. Try regular work or transfer funds.'
    if pockets < 200:
        if not has_unread_notification(pockets_msg):
            add_notification(user, pockets_msg, 'warning')

    loans = user.get('loans', {})
    total_debt = loans.get('regular', {}).get('currentDebt', 0) + loans.get('stock', {}).get('currentDebt', 0)
    debt_msg = '💡 Helper: Your debt is high. Consider paying loans before new investments.'
    if total_debt > 20000:
        if not has_unread_notification(debt_msg):
            add_notification(user, debt_msg, 'warning')

def get_advisor(user):
    ensure_runtime_fields(user)
    advisor = user.get('advisor', 'none')
    if advisor not in ADVISOR_PROFILES:
        advisor = 'none'
        user['advisor'] = advisor
    return advisor

def has_sufficient_funds(user, amount):
    """Check if user has enough money across pockets, checking, and savings."""
    total = user.get('pockets', 0) + user.get('checking', 0) + user.get('savings', 0)
    return total >= amount

def deduct_funds(user, amount):
    """Deduct funds from user accounts in order: pockets, checking, savings."""
    remaining = amount
    
    # First, deduct from pockets
    pockets = user.get('pockets', 0)
    if pockets >= remaining:
        user['pockets'] = pockets - remaining
        return
    else:
        user['pockets'] = 0
        remaining -= pockets
    
    # Then, deduct from checking
    checking = user.get('checking', 0)
    if checking >= remaining:
        user['checking'] = checking - remaining
        return
    else:
        user['checking'] = 0
        remaining -= checking
    
    # Finally, deduct from savings
    savings = user.get('savings', 0)
    user['savings'] = savings - remaining


def run_illegal_business_job(user, illegal_business):
    advisor = get_advisor(user)
    business_type = illegal_business.get('type', 'black_market')
    template = ILLEGAL_BUSINESS_TYPES.get(business_type, ILLEGAL_BUSINESS_TYPES['black_market'])

    payout = random.randint(template['min_payout'], template['max_payout'])
    raid_chance = template['base_raid_chance']

    if advisor == 'rivera':
        payout = int(payout * 1.2)
        raid_chance *= 0.65  # 35% lower chance of getting caught

    # Katie lifestyle effect makes all operations more expensive (reduced net gain)
    if advisor == 'katie':
        payout = int(payout * 0.85)

    caught = random.random() < raid_chance
    if caught:
        fine = int(payout * 0.8)
        jail_ms = 120000

        if advisor == 'rivera':
            # Rivera downside: when caught, punishment hits harder
            fine *= 3
            jail_ms *= 3
        elif advisor == 'miranda':
            fine = int(fine * 0.65)
            jail_ms = int(jail_ms * 0.75)

        user['pockets'] = max(0, user.get('pockets', 0) - fine)
        jail_user(user.get('id_for_runtime', session.get('player_id')), jail_ms)

        return {
            'success': False,
            'caught': True,
            'fine': fine,
            'jail_ms': jail_ms,
            'raid_chance': raid_chance,
            'message': f"🚨 Police raid! Operation failed. Fine: ${fine:,}. Jail: {int(jail_ms/60000)} minute(s)."
        }

    user['pockets'] = user.get('pockets', 0) + payout
    illegal_business['runs'] = illegal_business.get('runs', 0) + 1
    illegal_business['totalEarnings'] = illegal_business.get('totalEarnings', 0) + payout

    return {
        'success': True,
        'caught': False,
        'payout': payout,
        'raid_chance': raid_chance,
        'message': f"💰 Illegal operation successful! You earned ${payout:,}."
    }


def get_illegal_risk_and_payout_preview(user, illegal_business):
    advisor = get_advisor(user)
    business_type = illegal_business.get('type', 'black_market')
    template = ILLEGAL_BUSINESS_TYPES.get(business_type, ILLEGAL_BUSINESS_TYPES['black_market'])

    base_raid_chance = template['base_raid_chance']
    raid_chance = base_raid_chance
    base_min_payout = template['min_payout']
    base_max_payout = template['max_payout']
    min_payout = base_min_payout
    max_payout = base_max_payout

    advisor_note = 'No advisor modifier'

    if advisor == 'rivera':
        raid_chance *= 0.65
        min_payout = int(min_payout * 1.2)
        max_payout = int(max_payout * 1.2)
        advisor_note = 'Rivera: raid chance -35%, payout +20%'
    elif advisor == 'katie':
        min_payout = int(min_payout * 0.85)
        max_payout = int(max_payout * 0.85)
        advisor_note = 'Katie: payout -15% (higher lifestyle costs)'

    return {
        'advisor': advisor,
        'advisorNote': advisor_note,
        'baseRaidChance': round(base_raid_chance, 4),
        'baseRaidPercent': round(base_raid_chance * 100, 1),
        'raidChance': round(raid_chance, 4),
        'raidPercent': round(raid_chance * 100, 1),
        'baseMinPayout': base_min_payout,
        'baseMaxPayout': base_max_payout,
        'minPayout': min_payout,
        'maxPayout': max_payout,
    }

def get_cooldown_remaining(user_id, key, cooldown_ms):
    users = load_users()
    if user_id not in users:
        return 0
    cooldowns = users[user_id].get('cooldowns', {})
    last = cooldowns.get(key, 0)
    remaining = (last + cooldown_ms) - (datetime.now().timestamp() * 1000)
    return max(0, remaining)

def set_cooldown(user_id, key):
    users = load_users()
    if user_id not in users:
        ensure_user(user_id)
    if 'cooldowns' not in users[user_id]:
        users[user_id]['cooldowns'] = {}
    users[user_id]['cooldowns'][key] = datetime.now().timestamp() * 1000
    save_users(users)

def format_cooldown(ms):
    if ms <= 0:
        return '0s'
    seconds = int(ms / 1000)
    minutes = seconds // 60
    secs = seconds % 60
    if minutes > 0:
        return f'{minutes}m {secs}s'
    return f'{secs}s'

def is_jailed(user_id):
    users = load_users()
    if user_id not in users:
        return False
    jailed_until = users[user_id].get('jailedUntil', 0)
    return datetime.now().timestamp() * 1000 < jailed_until

def jail_user(user_id, duration_ms):
    users = load_users()
    ensure_user(user_id)
    users[user_id]['jailedUntil'] = datetime.now().timestamp() * 1000 + duration_ms
    users[user_id]['arrests'] = users[user_id].get('arrests', 0) + 1
    save_users(users)

# ==================== MYSTERY BOX SYSTEM ====================

def open_mystery_box(user, tier, quantity):
    """Open mystery boxes and award random items."""
    shop = load_shop()
    rewards = []
    
    # Define loot tables per tier
    if tier == 3:  # $200 - Basics
        loot_table = [
            ('cookie', 5, 20),  # item_id, min, max quantity
            ('jar', 3, 15),
            ('pinkfeet', 2, 10),
            ('feetpic', 2, 12),
            ('animefigurine', 1, 3),
            ('silverbar', 1, 2),
        ]
    elif tier == 2:  # $2,000 - Regular cars + collectibles
        loot_table = [
            ('toyoda_coralla', 1, 1),
            ('fard_fiesta', 1, 1),
            ('handa_civic', 1, 1),
            ('fard_fusion', 1, 1),
            ('toyoda_camree', 1, 1),
            ('nissin_altima', 1, 1),
            ('goldbar', 1, 3),
            ('silverbar', 2, 5),
            ('ruby', 1, 1),
            ('animefigurine', 2, 5),
        ]
    else:  # tier == 1, $25,000 - Luxury items
        loot_table = [
            ('linkkon_navigator', 1, 1),
            ('bmv_7series', 1, 1),
            ('mercades_sclass', 1, 1),
            ('porsh_911', 1, 1),
            ('lamborguini_huracan', 1, 1),
            ('goldbar', 3, 10),
            ('platinum', 2, 5),
            ('diamond', 1, 3),
            ('emerald', 1, 3),
            ('rolex', 1, 2),
            ('painting', 1, 2),
            ('tosla_modely', 1, 1),
            ('audi_r8', 1, 1),
        ]
    
    for _ in range(quantity):
        # Pick a random item from the loot table
        item_id, min_qty, max_qty = random.choice(loot_table)
        qty = random.randint(min_qty, max_qty)
        
        # Add to user's inventory
        if 'inventory' not in user:
            user['inventory'] = {}
        user['inventory'][item_id] = user['inventory'].get(item_id, 0) + qty
        
        # Get item name for reward display
        item_name = shop.get(item_id, {}).get('name', item_id)
        rewards.append({
            'item_id': item_id,
            'name': item_name,
            'quantity': qty
        })
    
    return rewards

# ==================== HELPER FUNCTIONS FOR QUICK WINS ====================

def add_transaction(user, type, amount, description):
    """Add transaction to user's history."""
    if 'transactions' not in user:
        user['transactions'] = []
    
    transaction = {
        'id': secrets.token_hex(8),
        'type': type,  # 'earn', 'spend', 'transfer', 'deposit', 'withdraw'
        'amount': amount,
        'description': description,
        'timestamp': datetime.now().isoformat()
    }
    
    user['transactions'].append(transaction)
    # Keep only last 200 transactions
    user['transactions'] = user['transactions'][-200:]
    
    # Update profile stats
    if type in ['earn', 'deposit']:
        user['totalEarned'] = user.get('totalEarned', 0) + amount
    elif type == 'spend':
        user['totalSpent'] = user.get('totalSpent', 0) + amount

def check_and_award_login_bonus(user):
    """Check if user is eligible for daily login bonus and award it."""
    now = datetime.now()
    last_bonus = user.get('lastLoginBonus')
    
    # Update login tracking
    user['lastLogin'] = now.isoformat()
    user['totalLogins'] = user.get('totalLogins', 0) + 1
    
    # Check login streak
    if last_bonus:
        try:
            last_bonus_time = datetime.fromisoformat(last_bonus)
            hours_since_last = (now - last_bonus_time).total_seconds() / 3600
            
            # If logged in within 24-48 hours, maintain streak
            if 24 <= hours_since_last < 48:
                user['loginStreak'] = user.get('loginStreak', 0) + 1
            elif hours_since_last >= 48:
                # Broke streak
                user['loginStreak'] = 1
        except:
            user['loginStreak'] = 1
    else:
        user['loginStreak'] = 1
    
    # Award bonus if eligible (once per day)
    if last_bonus is None:
        # First login ever
        user['pockets'] = user.get('pockets', 0) + 1500
        user['lastLoginBonus'] = now.isoformat()
        add_transaction(user, 'earn', 1500, '🎁 Daily Login Bonus')
        add_notification(user, '🎁 Daily login bonus: $1,500! Login streak: 1 day', 'success')
    else:
        try:
            last_bonus_time = datetime.fromisoformat(last_bonus)
            hours_since = (now - last_bonus_time).total_seconds() / 3600
            
            if hours_since >= 24:
                # Award bonus
                bonus_amount = 1500
                streak = user.get('loginStreak', 1)
                
                # Bonus for streak (extra $100 per day, max +$500)
                streak_bonus = min(500, (streak - 1) * 100)
                total_bonus = bonus_amount + streak_bonus
                
                user['pockets'] = user.get('pockets', 0) + total_bonus
                user['lastLoginBonus'] = now.isoformat()
                add_transaction(user, 'earn', total_bonus, f'🎁 Daily Login Bonus (Streak: {streak})')
                
                if streak_bonus > 0:
                    add_notification(user, f'🎁 Daily login bonus: ${total_bonus:,}! Login streak: {streak} days (+${streak_bonus:,} bonus)', 'success')
                else:
                    add_notification(user, f'🎁 Daily login bonus: ${total_bonus:,}! Login streak: {streak} day', 'success')
        except:
            pass

def check_and_update_work_streak(user):
    """Check and update work streak."""
    now = datetime.now()
    today = now.date()
    last_work_date = user.get('lastWorkDate')
    
    if last_work_date:
        try:
            last_date = datetime.fromisoformat(last_work_date).date()
            days_since = (today - last_date).days
            
            if days_since == 0:
                # Same day, maintain streak
                pass
            elif days_since == 1:
                # Consecutive day, increment streak
                user['workStreak'] = user.get('workStreak', 0) + 1
            else:
                # Broke streak
                user['workStreak'] = 1
        except:
            user['workStreak'] = 1
    else:
        user['workStreak'] = 1
    
    user['lastWorkDate'] = now.isoformat()
    user['totalWorked'] = user.get('totalWorked', 0) + 1
    
    # Return streak bonus (extra 5% per day, max 50%)
    streak = user.get('workStreak', 1)
    bonus_multiplier = min(1.5, 1.0 + (streak - 1) * 0.05)
    return bonus_multiplier, streak

# ==================== ROUTES ====================

@bp.route('/_game_internal')
def index():
    if 'player_id' not in session:
        session['player_id'] = secrets.token_hex(8)
        ensure_user(session['player_id'])
    return render_template('game.html')

# ==================== BANKING ====================

@bp.route('/api/create_account', methods=['POST'])
def create_account():
    data = request.json
    account_type = data.get('type')
    user_id = session.get('player_id')
    
    users = load_users()
    user = users[user_id]
    
    if account_type not in ['checking', 'savings']:
        return jsonify({'error': 'Invalid account type'}), 400
    
    # Check if trying to create an account they already have
    if account_type == 'checking' and user.get('hasCheckingAccount', False):
        return jsonify({'error': 'You already have a checking account!'}), 400
    if account_type == 'savings' and user.get('hasSavingsAccount', False):
        return jsonify({'error': 'You already have a savings account!'}), 400
    
    # Mark that they've created at least one account
    user['createdAccount'] = True
    
    # Set the specific account type flag
    if account_type == 'checking':
        user['hasCheckingAccount'] = True
    else:
        user['hasSavingsAccount'] = True
    
    # If this is their first account, set it as the default accountType
    if not user.get('accountType'):
        user['accountType'] = account_type
        
    save_users(users)
    
    add_notification(user, f'🏦 {account_type.title()} account created successfully!', 'success')
    save_users(users)
    
    return jsonify({'success': True, 'message': f'Created {account_type} account!'})

@bp.route('/api/balance')
def get_balance():
    check_and_process_updates()
    user_id = session.get('player_id')
    user = ensure_user(user_id)
    
    # Check for wealth-based achievements
    check_all_achievements(user_id)
    
    # Check and award daily login bonus
    check_and_award_login_bonus(user)
    
    return jsonify({
        'checking': user.get('checking', 0),
        'savings': user.get('savings', 0),
        'pockets': user.get('pockets', 0),
        'emergency': user.get('emergency', 0),
        'accountType': user.get('accountType'),
        'hasAccount': user.get('createdAccount', False),
        'hasCheckingAccount': user.get('hasCheckingAccount', False),
        'hasSavingsAccount': user.get('hasSavingsAccount', False),
        'hasInsurance': user.get('hasInsurance', False),
        'loginStreak': user.get('loginStreak', 0),
        'workStreak': user.get('workStreak', 0)
    })

@bp.route('/api/deposit', methods=['POST'])
def deposit():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        amount = int(data.get('amount', 0))
        target = data.get('target')
        user_id = session.get('player_id')
        
        if not user_id:
            return jsonify({'error': 'Not logged in'}), 400
        
        users = load_users()
        if user_id not in users:
            return jsonify({'error': 'User not found'}), 400
            
        user = users[user_id]
    except Exception as e:
        return jsonify({'error': f'Request error: {str(e)}'}), 400
    
    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
    
    if user['pockets'] < amount:
        return jsonify({'error': 'Not enough in pockets'}), 400
    
    if target == 'checking':
        if not user.get('hasCheckingAccount', False):
            return jsonify({'error': 'Create a checking account first'}), 400
        user['checking'] += amount
        user['pockets'] -= amount
    elif target == 'savings':
        if not user.get('hasSavingsAccount', False):
            return jsonify({'error': 'Create a savings account first'}), 400
        user['savings'] += amount
        user['pockets'] -= amount
    elif target == 'emergency':
        config = load_config()
        cap = config['emergencyCap']
        current = user.get('emergency', 0)
        space = max(0, cap - current)
        if space <= 0:
            return jsonify({'error': 'Emergency fund is full!'}), 400
        to_add = min(space, amount)
        user['emergency'] += to_add
        user['pockets'] -= to_add
        amount = to_add
    else:
        return jsonify({'error': 'Invalid target'}), 400
    
    save_users(users)
    return jsonify({'success': True, 'amount': amount})

@bp.route('/api/withdraw', methods=['POST'])
def withdraw():
    data = request.json
    amount = int(data.get('amount', 0))
    source = data.get('source')
    user_id = session.get('player_id')
    
    users = load_users()
    user = users[user_id]
    
    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
    
    if source == 'checking':
        if not user.get('hasCheckingAccount', False):
            return jsonify({'error': 'Create a checking account first'}), 400
        if user['checking'] < amount:
            return jsonify({'error': 'Not enough in checking'}), 400
        user['checking'] -= amount
        user['pockets'] += amount
    elif source == 'savings':
        if not user.get('hasSavingsAccount', False):
            return jsonify({'error': 'Create a savings account first'}), 400
        if user['savings'] < amount:
            return jsonify({'error': 'Not enough in savings'}), 400
        user['savings'] -= amount
        user['pockets'] += amount
    elif source == 'emergency':
        if user['emergency'] < amount:
            return jsonify({'error': 'Not enough in emergency fund'}), 400
        user['emergency'] -= amount
        user['pockets'] += amount
    else:
        return jsonify({'error': 'Invalid source'}), 400
    
    save_users(users)
    return jsonify({'success': True})

# ==================== WORK ====================

@bp.route('/api/work', methods=['POST'])
def work():
    user_id = session.get('player_id')
    
    if is_jailed(user_id):
        return jsonify({'error': 'You are in jail!'}), 400
    
    remaining = get_cooldown_remaining(user_id, 'work', 10000)  # 10 second cooldown
    if remaining > 0:
        return jsonify({'error': f'Cooldown: {format_cooldown(remaining)}'}), 400
    
    set_cooldown(user_id, 'work')
    
    amount = random.randint(50, 200)
    
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    advisor = get_advisor(user)
    
    # Check and update work streak
    streak_multiplier, streak = check_and_update_work_streak(user)
    amount = int(amount * streak_multiplier)

    if advisor == 'miranda':
        amount = int(amount * 0.85)

    message = random.choice(WORK_MESSAGES).replace('${amount}', str(amount))
    if streak > 1:
        message += f" (🔥 {streak} day streak: +{int((streak_multiplier - 1) * 100)}% bonus!)"

    user['pockets'] = user.get('pockets', 0) + amount
    add_transaction(user, 'earn', amount, f'Regular Work (Streak: {streak})')
    maybe_add_helper_notifications(user)
    save_users(users)
    
    # Update achievement stats
    update_achievement_stat(user_id, 'regular_jobs', 1)
    update_achievement_stat(user_id, 'total_jobs', 1)
    
    # Check for new achievements
    check_all_achievements(user_id)
    
    return jsonify({
        'success': True,
        'message': message,
        'amount': amount,
        'pockets': user['pockets'],
        'workStreak': streak
    })

@bp.route('/api/workgov', methods=['POST'])
def workgov():
    user_id = session.get('player_id')
    
    if is_jailed(user_id):
        return jsonify({'error': 'You are in jail!'}), 400
    
    remaining = get_cooldown_remaining(user_id, 'workgov', 120000)  # 2 minute cooldown
    if remaining > 0:
        return jsonify({'error': f'Cooldown: {format_cooldown(remaining)}'}), 400
    
    config = load_config()
    
    # Check for government shutdown
    if config.get('govShutdown', False):
        message = random.choice(SHUTDOWN_MESSAGES)
        return jsonify({
            'success': True,
            'message': message,
            'amount': 0,
            'shutdown': True
        })
    
    set_cooldown(user_id, 'workgov')
    
    gross_amount = random.randint(7500, 30000)
    tax_rate = config.get('govTaxPercent', 21)
    net_amount = int(gross_amount * (1 - tax_rate / 100))
    tax_collected = gross_amount - net_amount
    
    # Distribute tax to government departments
    if 'departmentBudgets' not in config:
        config['departmentBudgets'] = {
            'transportation': 0,
            'justice': 0,
            'defense': 0,
            'homeland': 0,
            'health': 0,
            'housing': 0,
            'education': 0
        }
    
    # Split tax evenly across all 7 departments
    per_department = tax_collected / 7
    config['departmentBudgets']['transportation'] += per_department
    config['departmentBudgets']['justice'] += per_department
    config['departmentBudgets']['defense'] += per_department
    config['departmentBudgets']['homeland'] += per_department
    config['departmentBudgets']['health'] += per_department
    config['departmentBudgets']['housing'] += per_department
    config['departmentBudgets']['education'] += per_department
    save_config(config)
    
    job_desc = random.choice(GOV_MESSAGES)
    message = f"{job_desc} and made ${gross_amount:,} but taxes apply at {tax_rate}% so you only brought home ${net_amount:,}"
    
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    advisor = get_advisor(user)
    
    # Check for loan collections
    collection_amount = 0
    deducted_amount = 0
    loans = user.get('loans', {})
    regular_loan = loans.get('regular', {})
    stock_loan = loans.get('stock', {})
    
    regular_debt = max(0, int(regular_loan.get('currentDebt', 0) or 0))
    stock_debt = max(0, int(stock_loan.get('currentDebt', 0) or 0))
    total_debt = regular_debt + stock_debt
    
    if total_debt > 0:
        # Collect 25% of net pay
        collection_amount = int(net_amount * 0.25)
        deducted_amount = collection_amount
        net_amount -= collection_amount
        
        # Apply to regular loan first, then stock loan
        if regular_loan.get('currentDebt', 0) > 0:
            payment = min(collection_amount, regular_loan['currentDebt'])
            regular_loan['currentDebt'] -= payment
            collection_amount -= payment
        
        if collection_amount > 0 and stock_loan.get('currentDebt', 0) > 0:
            payment = min(collection_amount, stock_loan['currentDebt'])
            stock_loan['currentDebt'] -= payment
        
        if deducted_amount > 0:
            message += f"\n⚠️ LOAN COLLECTIONS: ${deducted_amount:,} deducted for outstanding loans"

    if advisor == 'miranda':
        net_amount = int(net_amount * 0.9)
        message += "\n⚖️ MIRANDA EFFECT: cautious strategy reduces short-term gains."
    
    user['pockets'] = user.get('pockets', 0) + net_amount
    maybe_add_helper_notifications(user)
    save_users(users)
    
    # Update achievement stats
    update_achievement_stat(user_id, 'gov_jobs', 1)
    update_achievement_stat(user_id, 'total_jobs', 1)
    
    # Check for new achievements
    check_all_achievements(user_id)
    
    return jsonify({
        'success': True,
        'message': message,
        'gross': gross_amount,
        'net': net_amount,
        'tax_rate': tax_rate,
        'pockets': user['pockets']
    })

# ==================== BUSINESSES ====================

# Business upgrade costs and benefits
UPGRADE_TIERS = {
    'capacity': [
        {'level': 1, 'cost': 50000, 'capacity': 10, 'name': 'Small'},
        {'level': 2, 'cost': 150000, 'capacity': 25, 'name': 'Medium'},
        {'level': 3, 'cost': 400000, 'capacity': 50, 'name': 'Large'},
        {'level': 4, 'cost': 1000000, 'capacity': 100, 'name': 'Very Large'},
        {'level': 5, 'cost': 5000000, 'capacity': 250, 'name': 'Massive'}
    ],
    'automation': [
        {'level': 1, 'cost': 100000, 'bonus': 0.1, 'name': 'Auto-Restock'},
        {'level': 2, 'cost': 250000, 'bonus': 0.15, 'name': 'Auto-Hire'},
        {'level': 3, 'cost': 500000, 'bonus': 0.25, 'name': 'Smart Pricing'},
        {'level': 4, 'cost': 2000000, 'bonus': 0.4, 'name': 'Full Autopilot'}
    ],
    'quality': [
        {'level': 1, 'cost': 75000, 'bonus': 0.1, 'name': 'Marketing'},
        {'level': 2, 'cost': 200000, 'bonus': 0.2, 'name': 'Premium Service'},
        {'level': 3, 'cost': 350000, 'bonus': 0.35, 'name': 'Brand Recognition'}
    ],
    'location': [
        {'level': 1, 'cost': 50000, 'traffic': 1.0, 'name': 'Suburb'},
        {'level': 2, 'cost': 200000, 'traffic': 1.5, 'name': 'City Center'},
        {'level': 3, 'cost': 800000, 'traffic': 2.5, 'name': 'Downtown'},
        {'level': 4, 'cost': 3000000, 'traffic': 4.0, 'name': 'Prime Location'}
    ]
}

# Employee roles and costs
EMPLOYEE_TYPES = {
    'cashier': {'cost': 5000, 'salary': 1000, 'revenue': 500},
    'specialist': {'cost': 15000, 'salary': 3000, 'revenue': 1500},
    'manager': {'cost': 30000, 'salary': 5000, 'revenue': 3000},
    'executive': {'cost': 50000, 'salary': 10000, 'revenue': 5000}
}

def init_business_structure(business):
    """Initialize business with all required fields including new features"""
    # Basic info
    if 'employees' not in business:
        business['employees'] = []
    if 'workers' not in business:
        business['workers'] = 0
    if 'regular_workers' not in business:  # NEW: Bulk workers (like Ford's 55,000)
        business['regular_workers'] = 0
    if 'worker_wage' not in business:  # NEW: Daily wage per regular worker
        business['worker_wage'] = 100  # Default $100/day per worker
    
    # Upgrades
    if 'upgrades' not in business:
        business['upgrades'] = {
            'capacity': 0,
            'automation': 0,
            'quality': 0,
            'location': 0
        }
    
    # Revenue tracking
    if 'dailyRevenue' not in business:
        business['dailyRevenue'] = 0
    if 'revenue' not in business:
        business['revenue'] = 0
    if 'totalEarnings' not in business:
        business['totalEarnings'] = 0
    if 'totalGrossRevenue' not in business:
        business['totalGrossRevenue'] = 0
    if 'totalSalariesPaid' not in business:
        business['totalSalariesPaid'] = 0
    if 'totalTaxesPaid' not in business:
        business['totalTaxesPaid'] = 0
    if 'lastRevenueAt' not in business:
        business['lastRevenueAt'] = datetime.now().isoformat()
    if 'expenses' not in business:
        business['expenses'] = 0
    
    # NEW: Business classification
    if 'size' not in business:
        business['size'] = 'solo'  # solo, partnership, major_service, corporation
    if 'industry' not in business:
        business['industry'] = 'general'
    
    # NEW: Legal structure
    if 'legal_structure' not in business:
        business['legal_structure'] = 'sole_proprietorship'
    
    # NEW: Partnerships
    if 'partners' not in business:
        business['partners'] = []  # [{'user_id': 'xxx', 'ownership_pct': 50, 'joined_at': 'iso'}]
    if 'partnership_requests' not in business:
        business['partnership_requests'] = []
    
    # NEW: Franchising
    if 'is_franchise_parent' not in business:
        business['is_franchise_parent'] = False
    if 'franchise_fee' not in business:
        business['franchise_fee'] = 0
    if 'franchise_royalty_rate' not in business:
        business['franchise_royalty_rate'] = 0.05  # 5%
    if 'franchisees' not in business:
        business['franchisees'] = []  # List of business_ids that are franchises
    if 'is_franchisee' not in business:
        business['is_franchisee'] = False
    if 'franchise_parent_id' not in business:
        business['franchise_parent_id'] = None
    
    # NEW: Insurance
    if 'insurance' not in business:
        business['insurance'] = []  # Active insurance policies
    
    # NEW: Loans
    if 'loans' not in business:
        business['loans'] = []  # Active business loans
    
    # NEW: IPO/Stock market
    if 'is_public' not in business:
        business['is_public'] = False
    if 'stock_symbol' not in business:
        business['stock_symbol'] = None
    if 'shares_outstanding' not in business:
        business['shares_outstanding'] = 0
    if 'shares_public' not in business:
        business['shares_public'] = 0
    if 'share_price' not in business:
        business['share_price'] = 0
    
    # NEW: Bankruptcy tracking
    if 'ever_bankrupt' not in business:
        business['ever_bankrupt'] = False
    if 'bankruptcy_count' not in business:
        business['bankruptcy_count'] = 0
    
    # NEW: Business age tracking
    if 'age_days' not in business:
        created_at = business.get('createdAt')
        if created_at:
            try:
                created = datetime.fromisoformat(created_at)
                business['age_days'] = (datetime.now() - created).days
            except:
                business['age_days'] = 0
        else:
            business['age_days'] = 0
    
    return business


def init_illegal_business_structure(illegal_business):
    """Initialize illegal business/criminal enterprise with all criminal features"""
    # Basic criminal operation info
    if 'criminal_workers' not in illegal_business:
        illegal_business['criminal_workers'] = {
            'enforcers': 0,
            'dealers': 0,
            'smugglers': 0,
            'hackers': 0,
            'lookouts': 0,
            'money_mules': 0
        }
    
    if 'worker_wages' not in illegal_business:
        illegal_business['worker_wages'] = {
            'enforcers': 500,
            'dealers': 300,
            'smugglers': 800,
            'hackers': 1000,
            'lookouts': 200,
            'money_mules': 400
        }
    
    # Heat/Suspicion level (opposite of reputation)
    if 'heat_level' not in illegal_business:
        illegal_business['heat_level'] = 0.1  # Starts at 10%, increases with activity
    if 'last_heat_decay' not in illegal_business:
        illegal_business['last_heat_decay'] = datetime.now().isoformat()
    if 'times_raided' not in illegal_business:
        illegal_business['times_raided'] = 0
    if 'times_escaped' not in illegal_business:
        illegal_business['times_escaped'] = 0
    
    # Criminal enterprise size
    if 'size' not in illegal_business:
        illegal_business['size'] = 'solo_operation'  # solo_operation, small_gang, crime_syndicate, cartel
    if 'category' not in illegal_business:
        illegal_business['category'] = 'black_market_goods'  # From ILLEGAL_BUSINESS_CATEGORIES
    
    # Territory control
    if 'territories' not in illegal_business:
        illegal_business['territories'] = []  # [{'area': 'downtown', 'control': 0.5}]
    if 'territory_wars' not in illegal_business:
        illegal_business['territory_wars'] = []  # Conflicts with other criminal operations
    
    # Criminal partnerships/alliances
    if 'criminal_partners' not in illegal_business:
        illegal_business['criminal_partners'] = []  # Similar to regular partnerships but for criminals
    if 'partnership_offers' not in illegal_business:
        illegal_business['partnership_offers'] = []
    
    # Money laundering
    if 'dirty_money' not in illegal_business:
        illegal_business['dirty_money'] = 0  # Money that needs to be laundered
    if 'clean_money' not in illegal_business:
        illegal_business['clean_money'] = 0  # Laundered money
    if 'laundering_rate' not in illegal_business:
        illegal_business['laundering_rate'] = 0.7  # 30% loss during laundering
    if 'laundering_operations' not in illegal_business:
        illegal_business['laundering_operations'] = []  # Active laundering jobs
    
    # Protection & bribes
    if 'police_bribes_paid' not in illegal_business:
        illegal_business['police_bribes_paid'] = 0
    if 'bribe_level' not in illegal_business:
        illegal_business['bribe_level'] = 0  # 0-100, reduces raid chance
    if 'protection_cost' not in illegal_business:
        illegal_business['protection_cost'] = 0  # Daily cost to reduce heat
    
    # Criminal network influence
    if 'reputation' not in illegal_business:
        illegal_business['reputation'] = 0  # Criminal underworld reputation (opposite of legal reputation)
    if 'rival_gangs' not in illegal_business:
        illegal_business['rival_gangs'] = []  # Enemies in criminal world
    if 'allied_operations' not in illegal_business:
        illegal_business['allied_operations'] = []  # Friendly criminal organizations
    
    # Revenue tracking
    if 'daily_revenue' not in illegal_business:
        illegal_business['daily_revenue'] = 0
    if 'total_revenue' not in illegal_business:
        illegal_business['total_revenue'] = 0
    if 'total_wages_paid' not in illegal_business:
        illegal_business['total_wages_paid'] = 0
    if 'total_bribes_paid' not in illegal_business:
        illegal_business['total_bribes_paid'] = 0
    if 'total_laundered' not in illegal_business:
        illegal_business['total_laundered'] = 0
    
    # Seized assets (from raids)
    if 'assets_seized' not in illegal_business:
        illegal_business['assets_seized'] = 0
    if 'workers_arrested' not in illegal_business:
        illegal_business['workers_arrested'] = 0
    
    # Advisor bonuses (Rivera benefits)
    if 'advisor_bonuses' not in illegal_business:
        illegal_business['advisor_bonuses'] = {}
    
    # Existing fields from old system
    if 'runs' not in illegal_business:
        illegal_business['runs'] = 0
    if 'totalEarnings' not in illegal_business:
        illegal_business['totalEarnings'] = 0
    if 'history' not in illegal_business:
        illegal_business['history'] = []
    if 'lastOutcome' not in illegal_business:
        illegal_business['lastOutcome'] = None
    
    return illegal_business


def _ensure_department_budgets(config: dict) -> None:
    if not isinstance(config, dict):
        return
    if 'departmentBudgets' not in config or not isinstance(config.get('departmentBudgets'), dict):
        config['departmentBudgets'] = {
            'transportation': 0,
            'justice': 0,
            'defense': 0,
            'homeland': 0,
            'health': 0,
            'housing': 0,
            'education': 0
        }
        return

    for k in ('transportation', 'justice', 'defense', 'homeland', 'health', 'housing', 'education'):
        if k not in config['departmentBudgets']:
            config['departmentBudgets'][k] = 0


def _get_business_tax_rate(owner_user=None, config=None) -> float:
    """Return business tax rate as a fraction (e.g. 0.10 for 10%)."""
    cfg = config if isinstance(config, dict) else load_config()
    raw = cfg.get('taxRate', 0.1)
    try:
        rate = float(raw)
    except Exception:
        rate = 0.1

    # Allow either 0.10 or 10 style values.
    if rate > 1.0:
        rate = rate / 100.0

    advisor = 'none'
    try:
        if isinstance(owner_user, dict):
            advisor = get_advisor(owner_user)
    except Exception:
        advisor = 'none'

    # FUTURE_FEATURES: Miranda reduces business tax rate.
    if advisor == 'miranda':
        rate = max(0.0, rate - 0.05)

    return max(0.0, min(rate, 0.95))


def _apply_business_tax_to_config(config: dict, tax_collected: int) -> None:
    """Distribute business taxes into economy pools (FUTURE_FEATURES).

    70% -> department budgets
    20% -> savings interest pool
    10% -> infrastructure maintenance
    """
    if not isinstance(config, dict):
        return

    tax = max(0, _coerce_int_amount(tax_collected))
    if tax <= 0:
        return

    config['businessTaxPool'] = _coerce_int_amount(config.get('businessTaxPool', 0)) + tax

    gov_share = int(round(tax * 0.70))
    savings_share = int(round(tax * 0.20))
    infra_share = int(tax - gov_share - savings_share)

    config['savingsInterestPool'] = _coerce_int_amount(config.get('savingsInterestPool', 0)) + savings_share
    config['infrastructureMaintenancePool'] = _coerce_int_amount(config.get('infrastructureMaintenancePool', 0)) + infra_share

    _ensure_department_budgets(config)
    per_department = gov_share / 7
    for k in ('transportation', 'justice', 'defense', 'homeland', 'health', 'housing', 'education'):
        config['departmentBudgets'][k] = config['departmentBudgets'].get(k, 0) + per_department


def _business_ops_employee_cap(business: dict) -> int:
    """Compute maximum employee slots for a business based on capacity upgrade."""
    try:
        upgrades = business.get('upgrades', {}) if isinstance(business, dict) else {}
        tier = _coerce_int_amount(upgrades.get('capacity', 0))
        if tier <= 0:
            return 2
        tiers = UPGRADE_TIERS.get('capacity', [])
        if tier - 1 >= len(tiers):
            tier = len(tiers)
        capacity_value = _coerce_int_amount(tiers[tier - 1].get('capacity', 10)) if tiers else 10
        # Map customer capacity to employee slots (conservative).
        return max(2, int(round(capacity_value / 5)))
    except Exception:
        return 2


def _business_ops_snapshot(business: dict, owner_user=None) -> dict:
    """Compute current profit snapshot for a business (gross/salary/net and accumulated since lastRevenueAt).

    This is used for business-level management when a business_id is provided to Business Mode endpoints.
    """
    now = datetime.now()
    business = init_business_structure(business) if isinstance(business, dict) else {}

    # Base gross revenue per day by type (owner-operated baseline)
    base_gross_by_type = {
        'general': 2000,
        'retail': 2400,
        'restaurant': 2200,
        'tech': 3200,
    }
    base_gross_per_day = base_gross_by_type.get(str(business.get('type', 'general')), 2000)

    employees = business.get('employees', [])
    if not isinstance(employees, list):
        employees = []

    upgrades = business.get('upgrades', {})
    if not isinstance(upgrades, dict):
        upgrades = {}

    # Revenue and salary per day from employees
    emp_gross_per_day = 0
    emp_salary_per_day = 0
    normalized_employees = []
    for emp in employees:
        if not isinstance(emp, dict):
            continue
        emp_type = (emp.get('type') or emp.get('employee_type') or emp.get('role') or '').strip().lower()
        if emp_type in EMPLOYEE_TYPES:
            info = EMPLOYEE_TYPES[emp_type]
            emp_gross_per_day += _coerce_int_amount(info.get('revenue', 0))
            emp_salary_per_day += _coerce_int_amount(info.get('salary', 0))
            hired_at = (
                emp.get('hired_at')
                or emp.get('hiredAt')
                or emp.get('hired')
                or emp.get('hired_on')
                or emp.get('hiredOn')
                or emp.get('hired_date')
                or emp.get('hiredDate')
            )
            hired_at = str(hired_at) if hired_at else now.isoformat()
            normalized_employees.append({
                'type': emp_type,
                'hired_at': hired_at,
                'salary_per_day': _coerce_int_amount(info.get('salary', 0)),
                'revenue_per_day': _coerce_int_amount(info.get('revenue', 0)),
            })

    revenue_multiplier = 1.0
    salary_multiplier = 1.0

    # Quality upgrade: boosts revenue
    q_tier = _coerce_int_amount(upgrades.get('quality', 0))
    if q_tier > 0 and q_tier - 1 < len(UPGRADE_TIERS.get('quality', [])):
        revenue_multiplier *= (1.0 + float(UPGRADE_TIERS['quality'][q_tier - 1].get('bonus', 0)))

    # Automation: boosts revenue and slightly reduces salary burden
    a_tier = _coerce_int_amount(upgrades.get('automation', 0))
    if a_tier > 0 and a_tier - 1 < len(UPGRADE_TIERS.get('automation', [])):
        bonus = float(UPGRADE_TIERS['automation'][a_tier - 1].get('bonus', 0))
        revenue_multiplier *= (1.0 + bonus)
        salary_multiplier *= max(0.6, 1.0 - (bonus * 0.5))

    # Location: traffic multiplier
    l_tier = _coerce_int_amount(upgrades.get('location', 0))
    if l_tier > 0 and l_tier - 1 < len(UPGRADE_TIERS.get('location', [])):
        traffic = float(UPGRADE_TIERS['location'][l_tier - 1].get('traffic', 1.0))
        revenue_multiplier *= max(0.1, traffic)

    gross_per_day = int((base_gross_per_day + emp_gross_per_day) * revenue_multiplier)
    salary_per_day = int(emp_salary_per_day * salary_multiplier)

    # NEW: Add regular workers contribution and costs
    regular_workers = _coerce_int_amount(business.get('regular_workers', 0))
    worker_wage = _coerce_int_amount(business.get('worker_wage', 100))
    
    if regular_workers > 0:
        # Each regular worker generates revenue (less than AI employees, but scalable)
        workers_revenue_per_day = regular_workers * 200  # $200 revenue per worker per day
        workers_salary_per_day = regular_workers * worker_wage
        
        # Add to totals
        gross_per_day += int(workers_revenue_per_day * revenue_multiplier)
        salary_per_day += workers_salary_per_day

    # Advisor business effects (FUTURE_FEATURES)
    advisor = 'none'
    try:
        if isinstance(owner_user, dict):
            advisor = get_advisor(owner_user)
    except Exception:
        advisor = 'none'

    if advisor == 'gina':
        gross_per_day = int(gross_per_day * 1.15)
        salary_per_day = int(salary_per_day * 0.90)
    elif advisor == 'katie':
        gross_per_day = int(gross_per_day * 1.10)

    config = load_config()
    tax_rate = _get_business_tax_rate(owner_user=owner_user, config=config)
    tax_per_day = int(gross_per_day * tax_rate)
    net_per_day = max(0, gross_per_day - salary_per_day - tax_per_day)

    # Accumulated since lastRevenueAt
    last_iso = business.get('lastRevenueAt') or now.isoformat()
    try:
        last_dt = datetime.fromisoformat(str(last_iso))
    except Exception:
        last_dt = now

    hours_elapsed = max(0.0, (now - last_dt).total_seconds() / 3600.0)

    accumulated_gross = int((gross_per_day / 24.0) * hours_elapsed)
    accumulated_salary = int((salary_per_day / 24.0) * hours_elapsed)
    accumulated_tax = int((tax_per_day / 24.0) * hours_elapsed)
    accumulated_net = int((net_per_day / 24.0) * hours_elapsed)

    max_employees = _business_ops_employee_cap(business)

    return {
        'employees_normalized': normalized_employees,
        'employee_count': len(normalized_employees),
        'max_employees': max_employees,
        'regular_workers': regular_workers,
        'worker_wage': worker_wage,
        'upgrades': upgrades,
        'gross_per_day': gross_per_day,
        'salary_per_day': salary_per_day,
        'tax_rate': tax_rate,
        'tax_per_day': tax_per_day,
        'net_per_day': net_per_day,
        'net_per_hour': int(net_per_day / 24.0),
        'hours_elapsed': hours_elapsed,
        'accumulated_gross': max(0, accumulated_gross),
        'accumulated_salary': max(0, accumulated_salary),
        'accumulated_tax': max(0, accumulated_tax),
        'accumulated_profit': max(0, accumulated_net),
    }

@bp.route('/api/create_business', methods=['POST'])
def create_business():
    data = request.json
    business_name = data.get('name', '').strip()
    business_type = data.get('type', 'general')
    industry = data.get('industry', 'general')  # NEW: Industry selection
    user_id = session.get('player_id')
    
    if not business_name or len(business_name) < 3:
        return jsonify({'error': 'Business name must be at least 3 characters'}), 400
    
    # Validate industry
    if industry not in BUSINESS_INDUSTRIES:
        industry = 'general'
    
    cost = 50000  # Cost to create a business
    
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    advisor = get_advisor(user)

    if advisor == 'katie':
        cost = int(cost * 1.2)
    
    if not has_sufficient_funds(user, cost):
        return jsonify({'error': f'Need ${cost:,} to create a business. You don\'t have enough money.'}), 400
    
    businesses = load_businesses()
    business_id = secrets.token_hex(8)
    
    businesses[business_id] = init_business_structure({
        'id': business_id,
        'name': business_name,
        'type': business_type,
        'industry': industry,  # NEW
        'size': 'solo',  # NEW: Start as solo business
        'owner': user_id,
        'revenue': 0,
        'totalEarnings': 0,
        'createdAt': datetime.now().isoformat()
    })
    
    user['businesses'].append(business_id)
    deduct_funds(user, cost)
    
    save_businesses(businesses)
    save_users(users)
    
    return jsonify({'success': True, 'business': businesses[business_id]})


@bp.route('/api/business/industries')
def get_business_industries():
    """Get available business industries"""
    return jsonify({
        'industries': BUSINESS_INDUSTRIES,
        'sizes': BUSINESS_SIZES,
        'legal_structures': LEGAL_STRUCTURES
    })


@bp.route('/api/illegal_business/categories')
def get_illegal_business_categories():
    """Get available illegal business categories and types"""
    return jsonify({
        'categories': ILLEGAL_BUSINESS_CATEGORIES,
        'sizes': ILLEGAL_BUSINESS_SIZES,
        'worker_types': CRIMINAL_WORKER_TYPES
    })


@bp.route('/api/businesses')
def get_businesses():
    check_and_process_updates()
    user_id = session.get('player_id')
    user = ensure_user(user_id)
    
    businesses = load_businesses()
    users = load_users()
    owner_user = users.get(user_id, {}) if isinstance(users, dict) else {}
    ensure_runtime_fields(owner_user) if isinstance(owner_user, dict) else None

    user_businesses = []
    for bid in user.get('businesses', []):
        if bid not in businesses:
            continue
        biz = init_business_structure(businesses[bid])
        snap = _business_ops_snapshot(biz, owner_user=owner_user)
        payload = dict(biz)
        payload['workers'] = snap.get('employee_count', 0)
        payload['revenue'] = snap.get('net_per_hour', 0)
        user_businesses.append(payload)
    
    return jsonify({'businesses': user_businesses})


@bp.route('/api/create_illegal_business', methods=['POST'])
def create_illegal_business():
    data = request.json or {}
    user_id = session.get('player_id')
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)

    business_type = data.get('type', 'Black Market Stall')  # Now stores specific type name
    category = data.get('category', 'black_market_goods')  # NEW: Category from ILLEGAL_BUSINESS_CATEGORIES
    name = (data.get('name') or '').strip()

    if category not in ILLEGAL_BUSINESS_CATEGORIES:
        return jsonify({'error': 'Invalid illegal business category'}), 400

    cat_data = ILLEGAL_BUSINESS_CATEGORIES[category]
    
    # Calculate cost based on category
    min_cost, max_cost = cat_data.get('startup_cost_range', (50000, 500000))
    cost = random.randint(min_cost, int(max_cost * 0.3))  # Start at 30% of max
    
    advisor = get_advisor(user)
    
    # Rivera makes illegal businesses cheaper
    if advisor == 'rivera':
        cost = int(cost * 0.7)  # 30% discount
    elif advisor == 'katie':
        cost = int(cost * 1.2)  # Katie doesn't like crime

    if not has_sufficient_funds(user, cost):
        return jsonify({'error': f'Need ${cost:,} to start this operation. You don\'t have enough money.'}), 400

    business_id = secrets.token_hex(8)
    illegal_business = {
        'id': business_id,
        'type': business_type,
        'category': category,
        'name': name or business_type,
        'createdAt': datetime.now().isoformat(),
        'runs': 0,
        'totalEarnings': 0,
        'lastRunAt': None,
        'history': [],
        'lastOutcome': None,
    }
    
    # Initialize with full criminal enterprise structure
    illegal_business = init_illegal_business_structure(illegal_business)

    deduct_funds(user, cost)
    user['illegalBusinesses'].append(illegal_business)
    
    # ADD NOTIFICATION based on heat level
    heat_emoji = '🕶️' if advisor == 'rivera' else '⚠️'
    add_notification(user, f"{heat_emoji} New illegal operation started: {illegal_business['name']} | Heat: {int(illegal_business['heat_level']*100)}%", 'warning')
    save_users(users)

    return jsonify({'success': True, 'business': illegal_business, 'startup_cost': cost})


@bp.route('/api/illegal_businesses')
def list_illegal_businesses():
    user_id = session.get('player_id')
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)

    cooldown_ms = 180000
    payload_businesses = []
    for entry in user.get('illegalBusinesses', []):
        business_copy = dict(entry)
        preview = get_illegal_risk_and_payout_preview(user, entry)
        remaining = 0
        last_run_iso = business_copy.get('lastRunAt')
        if last_run_iso:
            try:
                last_run = datetime.fromisoformat(last_run_iso)
                remaining = max(0, cooldown_ms - int((datetime.now() - last_run).total_seconds() * 1000))
            except Exception:
                remaining = 0

        business_copy['cooldownRemainingMs'] = remaining
        business_copy['cooldownLabel'] = format_cooldown(remaining)
        business_copy['risk'] = preview
        payload_businesses.append(business_copy)

    return jsonify({'businesses': payload_businesses, 'types': ILLEGAL_BUSINESS_TYPES, 'cooldownMs': cooldown_ms})


@bp.route('/api/run_illegal_business', methods=['POST'])
def run_illegal_business():
    data = request.json or {}
    business_id = data.get('business_id')
    user_id = session.get('player_id')
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    user['id_for_runtime'] = user_id

    if is_jailed(user_id):
        del user['id_for_runtime']
        return jsonify({'error': 'You are in jail!'}), 400

    illegal_business = None
    for entry in user.get('illegalBusinesses', []):
        if entry.get('id') == business_id:
            illegal_business = entry
            break

    if not illegal_business:
        del user['id_for_runtime']
        return jsonify({'error': 'Illegal business not found'}), 404

    # Shared cooldown per illegal business
    cooldown_ms = 180000
    last_run_iso = illegal_business.get('lastRunAt')
    if last_run_iso:
        try:
            last_run = datetime.fromisoformat(last_run_iso)
            remaining = cooldown_ms - int((datetime.now() - last_run).total_seconds() * 1000)
            if remaining > 0:
                del user['id_for_runtime']
                return jsonify({'error': f'Cooldown: {format_cooldown(remaining)}'}), 400
        except Exception:
            pass

    result = run_illegal_business_job(user, illegal_business)
    illegal_business['lastRunAt'] = datetime.now().isoformat()

    outcome = {
        'at': datetime.now().isoformat(),
        'success': result.get('success', False),
        'caught': result.get('caught', False),
        'message': result.get('message'),
        'payout': result.get('payout', 0),
        'fine': result.get('fine', 0),
        'jail_ms': result.get('jail_ms', 0),
        'raid_chance': result.get('raid_chance', 0)
    }
    illegal_business['lastOutcome'] = outcome
    history = illegal_business.get('history', [])
    history.append(outcome)
    illegal_business['history'] = history[-15:]

    if result.get('caught'):
        add_notification(user, result['message'], 'danger')
    else:
        add_notification(user, result['message'], 'success')

    del user['id_for_runtime']
    save_users(users)

    payload = {
        'success': result['success'],
        'message': result['message'],
        'pockets': user.get('pockets', 0),
        'lastOutcome': illegal_business.get('lastOutcome')
    }
    if result.get('caught'):
        payload['fine'] = result['fine']
        payload['jail_ms'] = result['jail_ms']
    else:
        payload['payout'] = result['payout']

    return jsonify(payload)

@bp.route('/api/hire_worker', methods=['POST'])
def hire_worker():
    data = request.json
    business_id = data.get('business_id')
    user_id = session.get('player_id')
    
    businesses = load_businesses()
    if business_id not in businesses:
        return jsonify({'error': 'Business not found'}), 404
    
    business = businesses[business_id]
    if business['owner'] != user_id:
        return jsonify({'error': 'Not your business'}), 403
    
    cost_per_worker = 5000
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    advisor = get_advisor(user)

    if advisor == 'katie':
        cost_per_worker = int(cost_per_worker * 1.2)
    
    if not has_sufficient_funds(user, cost_per_worker):
        return jsonify({'error': f'Need ${cost_per_worker:,} to hire a worker. You don\'t have enough money.'}), 400
    
    deduct_funds(user, cost_per_worker)
    # Legacy worker system: keep count for backward compatibility.
    business['workers'] = business.get('workers', 0) + 1
    
    save_users(users)
    save_businesses(businesses)
    
    return jsonify({'success': True, 'workers': business['workers']})


# ==================== REGULAR WORKERS (BULK HIRING) ====================

@bp.route('/api/business/hire_regular_workers', methods=['POST'])
def hire_regular_workers():
    """Hire regular workers in bulk (like Ford's 55,000 workers)"""
    data = request.json or {}
    business_id = data.get('business_id')
    count = int(data.get('count', 1))
    user_id = session.get('player_id')
    
    if count <= 0 or count > 100000:
        return jsonify({'error': 'Invalid worker count (1-100,000)'}), 400
    
    businesses = load_businesses()
    if business_id not in businesses:
        return jsonify({'error': 'Business not found'}), 404
    
    business = init_business_structure(businesses[business_id])
    if business['owner'] != user_id:
        return jsonify({'error': 'Not your business'}), 403
    
    # Check business size limits
    size_limits = BUSINESS_SIZES.get(business.get('size', 'solo'), BUSINESS_SIZES['solo'])
    current_workers = business.get('regular_workers', 0)
    max_workers = size_limits['max_workers']
    
    if current_workers + count > max_workers:
        return jsonify({'error': f'Business size "{business.get("size")}" can only have {max_workers} regular workers. You currently have {current_workers}.'}), 400
    
    # Calculate hiring cost (one-time cost per worker + equipment)
    cost_per_worker = 500  # $500 hiring/training cost per worker
    total_cost = cost_per_worker * count
    
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    advisor = get_advisor(user)
    
    # Gina bonus: -10% employee costs
    if advisor == 'gina':
        total_cost = int(total_cost * 0.9)
    elif advisor == 'katie':
        total_cost = int(total_cost * 1.2)
    
    if not has_sufficient_funds(user, total_cost):
        return jsonify({'error': f'Need ${total_cost:,} to hire {count} workers.'}), 400
    
    deduct_funds(user, total_cost)
    business['regular_workers'] = current_workers + count
    
    save_users(users)
    save_businesses(businesses)
    
    return jsonify({
        'success': True,
        'regular_workers': business['regular_workers'],
        'hired': count,
        'cost': total_cost,
        'message': f'✅ Hired {count:,} regular workers for ${total_cost:,}'
    })


@bp.route('/api/business/fire_regular_workers', methods=['POST'])
def fire_regular_workers():
    """Fire regular workers in bulk"""
    data = request.json or {}
    business_id = data.get('business_id')
    count = int(data.get('count', 1))
    user_id = session.get('player_id')
    
    if count <= 0:
        return jsonify({'error': 'Invalid worker count'}), 400
    
    businesses = load_businesses()
    if business_id not in businesses:
        return jsonify({'error': 'Business not found'}), 404
    
    business = init_business_structure(businesses[business_id])
    if business['owner'] != user_id:
        return jsonify({'error': 'Not your business'}), 403
    
    current_workers = business.get('regular_workers', 0)
    
    if count > current_workers:
        count = current_workers
    
    # Severance cost (optional - makes it not free to fire)
    severance_per_worker = 200  # $200 severance per worker
    total_severance = severance_per_worker * count
    
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    
    # Deduct severance if user has funds (or it could be free)
    if has_sufficient_funds(user, total_severance):
        deduct_funds(user, total_severance)
    else:
        total_severance = 0  # No severance if can't afford
    
    business['regular_workers'] = current_workers - count
    
    save_users(users)
    save_businesses(businesses)
    
    return jsonify({
        'success': True,
        'regular_workers': business['regular_workers'],
        'fired': count,
        'severance_paid': total_severance,
        'message': f'✅ Fired {count:,} workers. Severance: ${total_severance:,}'
    })


@bp.route('/api/business/set_worker_wage', methods=['POST'])
def set_worker_wage():
    """Set daily wage for regular workers"""
    data = request.json or {}
    business_id = data.get('business_id')
    wage = int(data.get('wage', 100))
    user_id = session.get('player_id')
    
    if wage < 50 or wage > 1000:
        return jsonify({'error': 'Wage must be between $50-$1,000 per day'}), 400
    
    businesses = load_businesses()
    if business_id not in businesses:
        return jsonify({'error': 'Business not found'}), 404
    
    business = init_business_structure(businesses[business_id])
    if business['owner'] != user_id:
        return jsonify({'error': 'Not your business'}), 403
    
    business['worker_wage'] = wage
    save_businesses(businesses)
    
    return jsonify({
        'success': True,
        'worker_wage': wage,
        'message': f'✅ Set worker wage to ${wage}/day'
    })


@bp.route('/api/business/upgrade_size', methods=['POST'])
def upgrade_business_size():
    """Upgrade business size to unlock more workers/employees"""
    data = request.json or {}
    business_id = data.get('business_id')
    new_size = data.get('size', 'partnership')
    user_id = session.get('player_id')
    
    if new_size not in BUSINESS_SIZES:
        return jsonify({'error': 'Invalid business size'}), 400
    
    businesses = load_businesses()
    if business_id not in businesses:
        return jsonify({'error': 'Business not found'}), 404
    
    business = init_business_structure(businesses[business_id])
    if business['owner'] != user_id:
        return jsonify({'error': 'Not your business'}), 403
    
    current_size = business.get('size', 'solo')
    
    # Define upgrade path and costs
    size_order = ['solo', 'partnership', 'major_service', 'corporation']
    upgrade_costs = {
        'partnership': 100000,      # $100K
        'major_service': 500000,     # $500K
        'corporation': 5000000       # $5M
    }
    
    try:
        current_idx = size_order.index(current_size)
        new_idx = size_order.index(new_size)
    except ValueError:
        return jsonify({'error': 'Invalid size configuration'}), 400
    
    if new_idx <= current_idx:
        return jsonify({'error': 'Can only upgrade to larger size'}), 400
    
    if new_idx != current_idx + 1:
        return jsonify({'error': 'Must upgrade one level at a time'}), 400
    
    cost = upgrade_costs.get(new_size, 0)
    
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    
    if not has_sufficient_funds(user, cost):
        return jsonify({'error': f'Need ${cost:,} to upgrade to {BUSINESS_SIZES[new_size]["name"]}'}), 400
    
    deduct_funds(user, cost)
    business['size'] = new_size
    
    save_users(users)
    save_businesses(businesses)
    
    size_info = BUSINESS_SIZES[new_size]
    return jsonify({
        'success': True,
        'size': new_size,
        'name': size_info['name'],
        'max_employees': size_info['max_employees'],
        'max_workers': size_info['max_workers'],
        'message': f'✅ Upgraded to {size_info["name"]}! Can now have up to {size_info["max_workers"]:,} regular workers.'
    })


# ==================== PARTNERSHIPS (CO-OWNERSHIP) ====================

@bp.route('/api/business/send_partnership_request', methods=['POST'])
def send_partnership_request():
    """Send a partnership/co-ownership request to another player"""
    data = request.json or {}
    business_id = data.get('business_id')
    target_username = data.get('target_username', '').strip()
    ownership_pct = float(data.get('ownership_pct', 50.0))
    user_id = session.get('player_id')
    
    if not target_username:
        return jsonify({'error': 'Target username required'}), 400
    
    if ownership_pct <= 0 or ownership_pct >= 100:
        return jsonify({'error': 'Ownership % must be between 0-100'}), 400
    
    businesses = load_businesses()
    if business_id not in businesses:
        return jsonify({'error': 'Business not found'}), 404
    
    business = init_business_structure(businesses[business_id])
    if business['owner'] != user_id:
        return jsonify({'error': 'Not your business'}), 403
    
    # Check business size allows partners
    size_limits = BUSINESS_SIZES.get(business.get('size', 'solo'), BUSINESS_SIZES['solo'])
    current_partners = len(business.get('partners', []))
    max_partners = size_limits['max_partners']
    
    if current_partners >= max_partners:
        return jsonify({'error': f'Business size only allows {max_partners} partners'}), 400
    
    users = load_users()
    
    # Find target user
    target_user_id = None
    for uid, user_data in users.items():
        if user_data.get('username', '').lower() == target_username.lower():
            target_user_id = uid
            break
    
    if not target_user_id:
        return jsonify({'error': f'User "{target_username}" not found'}), 404
    
    if target_user_id == user_id:
        return jsonify({'error': 'Cannot partner with yourself'}), 400
    
    # Check if already a partner
    for partner in business.get('partners', []):
        if partner.get('user_id') == target_user_id:
            return jsonify({'error': 'Already a partner'}), 400
    
    # Check if request already pending
    for req in business.get('partnership_requests', []):
        if req.get('user_id') == target_user_id and req.get('status') == 'pending':
            return jsonify({'error': 'Partnership request already pending'}), 400
    
    # Create request
    request_data = {
        'id': secrets.token_hex(8),
        'user_id': target_user_id,
        'username': target_username,
        'ownership_pct': ownership_pct,
        'status': 'pending',
        'sent_at': datetime.now().isoformat()
    }
    
    if 'partnership_requests' not in business:
        business['partnership_requests'] = []
    business['partnership_requests'].append(request_data)
    
    # Add notification to target user
    target_user = users[target_user_id]
    ensure_runtime_fields(target_user)
    add_notification(
        target_user,
        f'🤝 Partnership offer from {users[user_id].get("username", "Unknown")} for {business.get("name", "Business")} ({ownership_pct}% ownership)',
        'info'
    )
    
    save_businesses(businesses)
    save_users(users)
    
    return jsonify({
        'success': True,
        'message': f'✅ Partnership request sent to {target_username}',
        'request': request_data
    })


@bp.route('/api/business/respond_partnership_request', methods=['POST'])
def respond_partnership_request():
    """Accept or decline a partnership request"""
    data = request.json or {}
    business_id = data.get('business_id')
    request_id = data.get('request_id')
    response = data.get('response', 'decline')  # 'accept' or 'decline'
    user_id = session.get('player_id')
    
    businesses = load_businesses()
    if business_id not in businesses:
        return jsonify({'error': 'Business not found'}), 404
    
    business = init_business_structure(businesses[business_id])
    
    # Find the request
    request_data = None
    for req in business.get('partnership_requests', []):
        if req.get('id') == request_id and req.get('user_id') == user_id:
            request_data = req
            break
    
    if not request_data:
        return jsonify({'error': 'Partnership request not found'}), 404
    
    if request_data.get('status') != 'pending':
        return jsonify({'error': 'Request already processed'}), 400
    
    users = load_users()
    owner_user = users.get(business['owner'], {})
    current_user = users.get(user_id, {})
    
    if response == 'accept':
        # Add as partner
        partner_entry = {
            'user_id': user_id,
            'username': current_user.get('username', 'Unknown'),
            'ownership_pct': request_data['ownership_pct'],
            'joined_at': datetime.now().isoformat()
        }
        
        if 'partners' not in business:
            business['partners'] = []
        business['partners'].append(partner_entry)
        
        # Add business to partner's list
        ensure_runtime_fields(current_user)
        if business_id not in current_user.get('businesses', []):
            current_user['businesses'].append(business_id)
        
        # Update request status
        request_data['status'] = 'accepted'
        request_data['responded_at'] = datetime.now().isoformat()
        
        # Notify owner
        ensure_runtime_fields(owner_user)
        add_notification(
            owner_user,
            f'🤝 {current_user.get("username", "Player")} accepted partnership in {business.get("name", "Business")}!',
            'success'
        )
        
        save_businesses(businesses)
        save_users(users)
        
        return jsonify({
            'success': True,
            'message': f'✅ You are now a {request_data["ownership_pct"]}% partner in {business.get("name", "Business")}!',
            'partner': partner_entry
        })
    else:
        # Decline
        request_data['status'] = 'declined'
        request_data['responded_at'] = datetime.now().isoformat()
        
        # Notify owner
        ensure_runtime_fields(owner_user)
        add_notification(
            owner_user,
            f'❌ {current_user.get("username", "Player")} declined partnership in {business.get("name", "Business")}',
            'warning'
        )
        
        save_businesses(businesses)
        save_users(users)
        
        return jsonify({
            'success': True,
            'message': 'Partnership request declined'
        })


@bp.route('/api/business/remove_partner', methods=['POST'])
def remove_partner():
    """Remove a partner from business (owner only)"""
    data = request.json or {}
    business_id = data.get('business_id')
    partner_user_id = data.get('partner_user_id')
    user_id = session.get('player_id')
    
    businesses = load_businesses()
    if business_id not in businesses:
        return jsonify({'error': 'Business not found'}), 404
    
    business = init_business_structure(businesses[business_id])
    if business['owner'] != user_id:
        return jsonify({'error': 'Only owner can remove partners'}), 403
    
    # Find and remove partner
    partner_found = False
    partner_data = None
    partners = business.get('partners', [])
    
    for i, partner in enumerate(partners):
        if partner.get('user_id') == partner_user_id:
            partner_data = partners.pop(i)
            partner_found = True
            break
    
    if not partner_found:
        return jsonify({'error': 'Partner not found'}), 404
    
    # Calculate buyout amount (90% of equity value)
    business_value = _estimate_business_value(business)
    ownership_value = int(business_value * (partner_data['ownership_pct'] / 100.0))
    buyout_amount = int(ownership_value * 0.90)
    
    users = load_users()
    owner_user = users[user_id]
    partner_user = users.get(partner_user_id, {})
    
    ensure_runtime_fields(owner_user)
    ensure_runtime_fields(partner_user)
    
    # Owner pays buyout
    if has_sufficient_funds(owner_user, buyout_amount):
        deduct_funds(owner_user, buyout_amount)
        partner_user['pockets'] = _coerce_int_amount(partner_user.get('pockets', 0)) + buyout_amount
        
        # Remove business from partner's list
        if business_id in partner_user.get('businesses', []):
            partner_user['businesses'].remove(business_id)
        
        # Notify partner
        add_notification(
            partner_user,
            f'💰 Bought out from {business.get("name", "Business")} for ${buyout_amount:,}',
            'info'
        )
        
        save_businesses(businesses)
        save_users(users)
        
        return jsonify({
            'success': True,
            'message': f'✅ Partner removed. Buyout: ${buyout_amount:,}',
            'buyout_amount': buyout_amount
        })
    else:
        return jsonify({'error': f'Need ${buyout_amount:,} to buy out partner'}), 400


def _estimate_business_value(business):
    """Estimate business value for partnerships/M&A"""
    total_earnings = business.get('totalEarnings', 0)
    revenue = business.get('revenue', 0)
    # Simple valuation: 10x annual earnings equivalent
    return max(100000, total_earnings * 10, revenue * 365)


# ==================== STOCKS ====================

@bp.route('/api/stocks')
def get_stocks():
    check_and_process_updates()
    stocks = load_stocks()
    return jsonify({'stocks': stocks})

@bp.route('/api/buy_stock', methods=['POST'])
def buy_stock():
    data = request.json
    symbol = data.get('symbol')
    quantity = int(data.get('quantity', 0))
    user_id = session.get('player_id')
    
    if quantity <= 0:
        return jsonify({'error': 'Invalid quantity'}), 400
    
    stocks = load_stocks()
    if symbol not in stocks:
        return jsonify({'error': 'Stock not found'}), 404
    
    stock_price = stocks[symbol]['price']
    total_cost = stock_price * quantity
    
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    advisor = get_advisor(user)

    if advisor == 'gina':
        total_cost = int(total_cost * 1.1)
    elif advisor == 'katie':
        total_cost = int(total_cost * 1.2)
    
    if not has_sufficient_funds(user, total_cost):
        return jsonify({'error': f'Need ${total_cost:,}. You don\'t have enough money.'}), 400
    
    deduct_funds(user, total_cost)
    
    if 'stocks' not in user:
        user['stocks'] = {}
    
    user['stocks'][symbol] = user['stocks'].get(symbol, 0) + quantity
    save_users(users)
    
    return jsonify({'success': True, 'total_cost': total_cost})

@bp.route('/api/sell_stock', methods=['POST'])
def sell_stock():
    data = request.json
    symbol = data.get('symbol')
    quantity = int(data.get('quantity', 0))
    user_id = session.get('player_id')
    
    if quantity <= 0:
        return jsonify({'error': 'Invalid quantity'}), 400
    
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    
    owned = user.get('stocks', {}).get(symbol, 0)
    if owned < quantity:
        return jsonify({'error': f'You only own {owned} shares'}), 400
    
    stocks = load_stocks()
    if symbol not in stocks:
        return jsonify({'error': 'Stock not found'}), 404
    
    stock_price = stocks[symbol]['price']
    total_revenue = stock_price * quantity

    advisor = get_advisor(user)
    if advisor == 'gina':
        total_revenue = int(total_revenue * 0.9)
    
    user['stocks'][symbol] -= quantity
    if user['stocks'][symbol] == 0:
        del user['stocks'][symbol]
    
    user['pockets'] = user.get('pockets', 0) + total_revenue
    save_users(users)
    
    return jsonify({'success': True, 'total_revenue': total_revenue})

@bp.route('/api/portfolio')
def get_portfolio():
    user_id = session.get('player_id')
    user = ensure_user(user_id)
    
    stocks = load_stocks()
    portfolio = []
    
    for symbol, quantity in user.get('stocks', {}).items():
        if symbol in stocks:
            stock = stocks[symbol]
            portfolio.append({
                'symbol': symbol,
                'name': stock['name'],
                'quantity': quantity,
                'currentPrice': stock['price'],
                'totalValue': stock['price'] * quantity
            })
    
    return jsonify({'portfolio': portfolio})

# ==================== CRYPTO ====================

@bp.route('/api/crypto')
def get_crypto():
    check_and_process_updates()
    crypto = load_crypto()
    return jsonify({'crypto': crypto})

@bp.route('/api/buy_crypto', methods=['POST'])
def buy_crypto():
    data = request.json
    symbol = data.get('symbol')
    amount = float(data.get('amount', 0))
    user_id = session.get('player_id')
    
    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
    
    crypto = load_crypto()
    if symbol not in crypto:
        return jsonify({'error': 'Crypto not found'}), 404
    
    crypto_price = crypto[symbol]['price']
    total_cost = int(amount * crypto_price)
    
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    advisor = get_advisor(user)

    if advisor == 'katie':
        total_cost = int(total_cost * 1.2)
    
    if not has_sufficient_funds(user, total_cost):
        return jsonify({'error': f'Need ${total_cost:,}. You don\'t have enough money.'}), 400
    
    deduct_funds(user, total_cost)
    
    if 'crypto' not in user:
        user['crypto'] = {}
    
    user['crypto'][symbol] = user['crypto'].get(symbol, 0) + amount
    save_users(users)
    
    return jsonify({'success': True, 'total_cost': total_cost})

@bp.route('/api/sell_crypto', methods=['POST'])
def sell_crypto():
    data = request.json
    symbol = data.get('symbol')
    amount = float(data.get('amount', 0))
    user_id = session.get('player_id')
    
    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
    
    users = load_users()
    user = users[user_id]
    
    owned = user.get('crypto', {}).get(symbol, 0)
    if owned < amount:
        return jsonify({'error': f'You only own {owned:.4f} {symbol}'}), 400
    
    crypto = load_crypto()
    if symbol not in crypto:
        return jsonify({'error': 'Crypto not found'}), 404
    
    crypto_price = crypto[symbol]['price']
    total_revenue = int(amount * crypto_price)
    
    user['crypto'][symbol] -= amount
    if user['crypto'][symbol] <= 0:
        del user['crypto'][symbol]
    
    user['pockets'] = user.get('pockets', 0) + total_revenue
    save_users(users)
    
    return jsonify({'success': True, 'total_revenue': total_revenue})

@bp.route('/api/crypto_wallet')
def get_crypto_wallet():
    user_id = session.get('player_id')
    user = ensure_user(user_id)
    
    crypto = load_crypto()
    wallet = []
    
    for symbol, amount in user.get('crypto', {}).items():
        if symbol in crypto:
            coin = crypto[symbol]
            wallet.append({
                'symbol': symbol,
                'name': coin['name'],
                'amount': amount,
                'currentPrice': coin['price'],
                'totalValue': int(coin['price'] * amount)
            })
    
    return jsonify({'wallet': wallet})

# ==================== S&P12 INDEX & STOCK DETAILS ====================

@bp.route('/api/sp12_index')
def get_sp12_index():
    """Get the S&P12 index value and component stocks."""
    stocks = load_stocks()
    
    # Calculate S&P12 index value (average of component prices, weighted by shares)
    sp12_stocks = []
    total_market_cap = 0
    
    for symbol, stock in stocks.items():
        if stock.get('sp12', False):
            market_cap = stock['price'] * stock.get('shares', 1000000)
            total_market_cap += market_cap
            sp12_stocks.append({
                'symbol': symbol,
                'name': stock['name'],
                'price': stock['price'],
                'change_points': stock.get('change_points', 0),
                'change_percent': round((stock.get('change_points', 0) / max(1, stock['price'] - stock.get('change_points', 0))) * 100, 2) if stock.get('change_points', 0) != 0 else 0,
                'shares': stock.get('shares', 1000000),
                'market_cap': market_cap
            })
    
    # Sort by market cap
    sp12_stocks.sort(key=lambda x: x['market_cap'], reverse=True)
    
    # Calculate index value (start at 1000 base)
    index_value = int((total_market_cap / 1000000000) * 100)  # Scaled value
    
    return jsonify({
        'index_value': index_value,
        'components': sp12_stocks,
        'total_market_cap': total_market_cap
    })

@bp.route('/api/stock/<symbol>/ownership')
def get_stock_ownership(symbol):
    """Get ownership breakdown for a specific stock."""
    stocks = load_stocks()
    if symbol not in stocks:
        return jsonify({'error': 'Stock not found'}), 404
    
    stock = stocks[symbol]
    total_shares = stock.get('shares', 1000000)
    
    # Get all users and their holdings
    users = load_users()
    ownership = []
    total_owned = 0
    
    for user_id, user in users.items():
        shares_owned = user.get('stocks', {}).get(symbol, 0)
        if shares_owned > 0:
            ownership.append({
                'username': user.get('username', user_id),
                'shares': shares_owned,
                'percentage': round((shares_owned / total_shares) * 100, 2)
            })
            total_owned += shares_owned
    
    # Sort by shares owned
    ownership.sort(key=lambda x: x['shares'], reverse=True)
    
    # Calculate unowned percentage
    unowned_shares = total_shares - total_owned
    unowned_pct = round((unowned_shares / total_shares) * 100, 2)
    
    return jsonify({
        'symbol': symbol,
        'name': stock['name'],
        'total_shares': total_shares,
        'total_owned': total_owned,
        'unowned_shares': unowned_shares,
        'unowned_percentage': unowned_pct,
        'ownership': ownership[:20]  # Top 20 owners
    })

# ==================== PROFILE & STATS ====================

@bp.route('/api/profile/stats')
def get_profile_stats():
    """Get user profile statistics."""
    user_id = session.get('player_id')
    user = ensure_user(user_id)
    
    # Calculate total wealth
    total_wealth = (
        user.get('pockets', 0) + 
        user.get('checking', 0) + 
        user.get('savings', 0) + 
        user.get('emergency', 0)
    )
    
    # Calculate account age
    created_at = user.get('accountCreatedAt')
    days_old = 0
    if created_at:
        try:
            created_date = datetime.fromisoformat(created_at)
            days_old = (datetime.now() - created_date).days
        except:
            pass
    
    return jsonify({
        'totalEarned': user.get('totalEarned', 0),
        'totalSpent': user.get('totalSpent', 0),
        'totalWorked': user.get('totalWorked', 0),
        'totalWealth': total_wealth,
        'loginStreak': user.get('loginStreak', 0),
        'workStreak': user.get('workStreak', 0),
        'totalLogins': user.get('totalLogins', 0),
        'accountAge': days_old,
        'accountCreatedAt': created_at,
        'achievements': len(user.get('achievements', {}).get('unlocked', [])),
        'businesses': len(user.get('businesses', [])),
        'illegalBusinesses': len(user.get('illegalBusinesses', []))
    })

@bp.route('/api/transactions')
def get_transactions():
    """Get user transaction history."""
    user_id = session.get('player_id')
    user = ensure_user(user_id)
    
    transactions = user.get('transactions', [])
    
    # Return most recent first
    transactions.reverse()
    
    return jsonify({
        'transactions': transactions[:100]  # Last 100 transactions
    })

# ==================== QUICK TRANSFER ====================

@bp.route('/api/quick_transfer', methods=['POST'])
def quick_transfer():
    """Quick transfer between checking and savings."""
    data = request.json
    amount = int(data.get('amount', 0))
    direction = data.get('direction', '')
    user_id = session.get('player_id')
    
    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
    
    users = load_users()
    user = users[user_id]
    
    # Support both old and new direction formats
    if direction in ['to_savings', 'checking_to_savings']:
        if user.get('checking', 0) < amount:
            return jsonify({'error': 'Insufficient checking balance'}), 400
        user['checking'] = user.get('checking', 0) - amount
        user['savings'] = user.get('savings', 0) + amount
        add_transaction(user, 'transfer', amount, 'Transfer: Checking → Savings')
        message = f'✅ Transferred ${amount:,} to savings'
    elif direction in ['to_checking', 'savings_to_checking']:
        if user.get('savings', 0) < amount:
            return jsonify({'error': 'Insufficient savings balance'}), 400
        user['savings'] = user.get('savings', 0) - amount
        user['checking'] = user.get('checking', 0) + amount
        add_transaction(user, 'transfer', amount, 'Transfer: Savings → Checking')
        message = f'✅ Transferred ${amount:,} to checking'
    else:
        return jsonify({'error': 'Invalid transfer direction'}), 400
    
    save_users(users)
    
    return jsonify({
        'success': True,
        'message': message,
        'amount': amount,
        'checking': user['checking'],
        'savings': user['savings']
    })

# ==================== LOANS ====================

@bp.route('/api/take_loan', methods=['POST'])
def take_loan():
    data = request.json
    loan_type = data.get('type', 'regular')
    amount = int(data.get('amount', 0))
    user_id = session.get('player_id')
    
    if amount <= 0 or amount > 100000:
        return jsonify({'error': 'Loan amount must be between $1 and $100,000'}), 400
    
    users = load_users()
    user = users[user_id]
    
    if 'loans' not in user:
        user['loans'] = {
            'regular': {'principal': 0, 'spent': 0, 'currentDebt': 0, 'missedDays': 0, 'inCollections': False, 'startDate': None},
            'stock': {'principal': 0, 'spent': 0, 'currentDebt': 0, 'inCollections': False, 'startDate': None}
        }
    
    loan = user['loans'].get(loan_type, {})
    
    if loan.get('currentDebt', 0) > 0:
        return jsonify({'error': f'You already have an active {loan_type} loan'}), 400
    
    loan['principal'] = amount
    loan['currentDebt'] = amount
    loan['spent'] = 0
    loan['startDate'] = datetime.now().isoformat()
    loan['inCollections'] = False
    
    user['pockets'] = user.get('pockets', 0) + amount
    
    save_users(users)
    
    return jsonify({'success': True, 'amount': amount})

@bp.route('/api/pay_loan', methods=['POST'])
def pay_loan():
    data = request.json
    loan_type = data.get('type', 'regular')
    amount = int(data.get('amount', 0))
    user_id = session.get('player_id')
    
    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
    
    users = load_users()
    user = users[user_id]
    
    loan = user.get('loans', {}).get(loan_type, {})
    current_debt = loan.get('currentDebt', 0)
    
    if current_debt == 0:
        return jsonify({'error': 'No active loan'}), 400
    
    if not has_sufficient_funds(user, amount):
        return jsonify({'error': 'Not enough money to make payment'}), 400
    
    payment = min(amount, current_debt)
    loan['currentDebt'] -= payment
    deduct_funds(user, payment)
    
    save_users(users)
    
    return jsonify({'success': True, 'paid': payment, 'remaining': loan['currentDebt']})

@bp.route('/api/loans')
def get_loans():
    user_id = session.get('player_id')
    user = ensure_user(user_id)
    
    loans = user.get('loans', {
        'regular': {'principal': 0, 'currentDebt': 0, 'inCollections': False},
        'stock': {'principal': 0, 'currentDebt': 0, 'inCollections': False}
    })
    
    config = load_config()
    
    return jsonify({
        'loans': loans,
        'interestRate': config.get('interestRate', 3)
    })

# ==================== SHOP ====================

@bp.route('/api/shop')
def get_shop():
    shop = load_shop()

    # Browsers can't JSON-parse Infinity/NaN. Represent unlimited maxOwn as null.
    safe_shop = {}
    for item_id, item in shop.items():
        safe_item = dict(item)
        max_own = safe_item.get('maxOwn', None)
        if isinstance(max_own, (int, float)) and (math.isinf(max_own) or math.isnan(max_own)):
            safe_item['maxOwn'] = None
        safe_shop[item_id] = safe_item

    return jsonify({'items': safe_shop})

@bp.route('/api/buy_item', methods=['POST'])
def buy_item():
    data = request.json
    item_id = data.get('item_id')
    quantity = int(data.get('quantity', 1))
    user_id = session.get('player_id')
    
    shop = load_shop()
    if item_id not in shop:
        return jsonify({'error': 'Item not found'}), 404
    
    item = shop[item_id]
    total_cost = item['price'] * quantity
    
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    advisor = get_advisor(user)

    if advisor == 'katie':
        total_cost = int(total_cost * 1.2)
    
    # Check max ownership
    current_owned = user.get('inventory', {}).get(item_id, 0)
    max_own = item.get('maxOwn', float('inf'))
    if max_own is None:
        max_own = float('inf')
    
    if current_owned + quantity > max_own:
        return jsonify({'error': f'Can only own {max_own} of this item'}), 400
    
    if not has_sufficient_funds(user, total_cost):
        return jsonify({'error': f'Need ${total_cost:,}. You don\'t have enough money.'}), 400
    
    deduct_funds(user, total_cost)
    
    # Special handling for mystery boxes - open immediately
    if item.get('type') == 'mystery_box':
        rewards = open_mystery_box(user, item.get('tier', 3), quantity)
        add_transaction(user, 'spend', total_cost, f'Purchased {quantity}x {item["name"]}')
        save_users(users)
        return jsonify({
            'success': True, 
            'total_cost': total_cost, 
            'mystery_box': True,
            'rewards': rewards
        })
    else:
        user['inventory'][item_id] = current_owned + quantity
        add_transaction(user, 'spend', total_cost, f'Purchased {quantity}x {item["name"]}')
        save_users(users)
        return jsonify({'success': True, 'total_cost': total_cost})

@bp.route('/api/inventory')
def get_inventory():
    user_id = session.get('player_id')
    user = ensure_user(user_id)
    
    shop = load_shop()
    inventory = []
    
    for item_id, quantity in user.get('inventory', {}).items():
        if item_id in shop:
            item = shop[item_id]
            inventory.append({
                'id': item_id,
                'name': item['name'],
                'quantity': quantity,
                'type': item.get('type', 'other')
            })
    
    return jsonify({'inventory': inventory})

# ==================== ROBBERY ====================

@bp.route('/api/rob/<target_id>', methods=['POST'])
def rob_user(target_id):
    user_id = session.get('player_id')
    
    if user_id == target_id:
        return jsonify({'error': 'Cannot rob yourself!'}), 400
    
    if is_jailed(user_id):
        return jsonify({'error': 'You are in jail!'}), 400
    
    remaining = get_cooldown_remaining(user_id, 'rob', 300000)  # 5 minute cooldown
    if remaining > 0:
        return jsonify({'error': f'Cooldown: {format_cooldown(remaining)}'}), 400
    
    users = load_users()
    
    if target_id not in users:
        return jsonify({'error': 'Target not found'}), 404
    
    target = users[target_id]
    user = users[user_id]
    ensure_runtime_fields(user)
    advisor = get_advisor(user)
    
    set_cooldown(user_id, 'rob')
    
    # 50% success rate (Rivera reduces caught chance by 35%)
    success_threshold = 0.5
    if advisor == 'rivera':
        success_threshold = 0.325

    success = random.random() > success_threshold
    
    if success:
        # Steal 10-30% of their pockets
        target_pockets = target.get('pockets', 0)
        steal_percent = random.uniform(0.1, 0.3)
        stolen_amount = int(target_pockets * steal_percent)
        
        if stolen_amount == 0:
            return jsonify({
                'success': False,
                'message': "They had nothing to steal!",
                'amount': 0
            })
        
        # Check if target has insurance
        if target.get('hasInsurance', False):
            # Insurance pays them back 50%
            insurance_payout = int(stolen_amount * 0.5)
            target['pockets'] += insurance_payout
            stolen_amount = int(stolen_amount * 0.5)  # You only get 50%
            message = random.choice(ROB_SUCCESS_MESSAGES).replace('${amount}', f'{stolen_amount:,}') + f"\n(They had insurance, so you only got half!)"
        else:
            target['pockets'] -= stolen_amount
            message = random.choice(ROB_SUCCESS_MESSAGES).replace('${amount}', f'{stolen_amount:,}')
        
        user['pockets'] = user.get('pockets', 0) + stolen_amount
        user['totalRobbedOthers'] = user.get('totalRobbedOthers', 0) + stolen_amount
        target['totalRobbedFrom'] = target.get('totalRobbedFrom', 0) + stolen_amount
        target['lastRobbedAmount'] = stolen_amount
        
        save_users(users)
        
        # Update achievement stats
        update_achievement_stat(user_id, 'successful_robberies', 1)
        update_achievement_stat(user_id, 'crime_streak', 1)
        
        # Check for new achievements
        check_all_achievements(user_id)
        
        return jsonify({
            'success': True,
            'message': message,
            'amount': stolen_amount
        })
    else:
        # Failed - go to jail for 2 minutes
        jail_duration = 120000
        if advisor == 'rivera':
            jail_duration = int(jail_duration * 3)
        elif advisor == 'miranda':
            jail_duration = int(jail_duration * 0.75)

        jail_user(user_id, jail_duration)
        message = random.choice(ROB_FAIL_MESSAGES)
        
        # Update achievement stats - reset crime streak
        update_achievement_stat(user_id, 'times_caught', 1)
        update_achievement_stat(user_id, 'crime_streak', 0, increment=False)  # Reset streak
        
        # Check for new achievements
        check_all_achievements(user_id)
        
        return jsonify({
            'success': False,
            'message': message + f" You're jailed for {int(jail_duration/60000)} minute(s)!",
            'jailed': True
        })

@bp.route('/api/buy_insurance', methods=['POST'])
def buy_insurance():
    user_id = session.get('player_id')
    
    cost = 10000
    
    users = load_users()
    user = users[user_id]
    
    if user.get('hasInsurance', False):
        return jsonify({'error': 'You already have insurance!'}), 400
    
    if not has_sufficient_funds(user, cost):
        return jsonify({'error': f'Insurance costs ${cost:,}. You don\'t have enough money.'}), 400
    
    deduct_funds(user, cost)
    user['hasInsurance'] = True
    
    save_users(users)
    
    return jsonify({'success': True, 'message': 'Insurance purchased!'})

# ==================== CONFIG/ADMIN ====================

@bp.route('/api/config')
def get_config():
    config = load_config()
    # Compute central bank vault live from all deposits.
    try:
        config['centralBankVault'] = compute_central_bank_vault()
    except Exception:
        # Never fail config fetch because of vault computation.
        pass
    return jsonify(config)


@bp.route('/api/owner/hourly-log')
def get_owner_hourly_log():
    if not session.get('is_owner'):
        return jsonify({'error': 'Owner access required'}), 403

    try:
        limit = int(request.args.get('limit', 50))
    except Exception:
        limit = 50
    limit = max(1, min(200, limit))

    entries = load_hourly_log()
    # Most recent first
    return jsonify({'entries': list(reversed(entries[-limit:]))})

@bp.route('/api/report_error', methods=['POST'])
def report_error():
    """Public endpoint to receive error reports from frontend."""
    try:
        data = request.json or {}
        error_entry = {
            'message': data.get('message', 'Unknown error'),
            'stack': data.get('stack', ''),
            'url': data.get('url', ''),
            'line': data.get('line', 0),
            'column': data.get('column', 0),
            'userAgent': data.get('userAgent', ''),
            'playerId': session.get('player_id', 'anonymous'),
            'username': data.get('username', 'anonymous')
        }
        append_error_log(error_entry)
        return jsonify({'success': True}), 200
    except Exception as e:
        # Don't let error reporting fail the app
        print(f"Error logging error: {e}")
        return jsonify({'success': False}), 500

@bp.route('/api/owner/errors')
def get_owner_errors():
    """Owner endpoint to view all error logs."""
    if not session.get('is_owner'):
        return jsonify({'error': 'Owner access required'}), 403
    
    try:
        limit = int(request.args.get('limit', 100))
    except Exception:
        limit = 100
    limit = max(1, min(500, limit))
    
    errors = load_error_logs()
    # Most recent first
    return jsonify({'errors': list(reversed(errors[-limit:]))})

@bp.route('/api/owner/clear_errors', methods=['POST'])
def clear_owner_errors():
    """Owner endpoint to clear all error logs."""
    if not session.get('is_owner'):
        return jsonify({'error': 'Owner access required'}), 403
    
    save_error_logs([])
    return jsonify({'success': True, 'message': 'All error logs cleared'})

@bp.route('/api/toggle_shutdown', methods=['POST'])
def toggle_shutdown():
    config = load_config()
    config['govShutdown'] = not config.get('govShutdown', False)
    save_config(config)
    return jsonify({'shutdown': config['govShutdown']})

@bp.route('/api/toggle_recession', methods=['POST'])
def toggle_recession():
    config = load_config()
    config['recession'] = not config.get('recession', False)
    save_config(config)
    return jsonify({'recession': config['recession']})

@bp.route('/api/advisors')
def get_advisors():
    user_id = session.get('player_id')
    user = ensure_user(user_id)
    advisor = get_advisor(user)
    return jsonify({'current': advisor, 'advisors': ADVISOR_PROFILES})

@bp.route('/api/advisor/select', methods=['POST'])
def select_advisor():
    user_id = session.get('player_id')
    data = request.json or {}
    advisor = (data.get('advisor') or 'none').strip().lower()

    if advisor not in ADVISOR_PROFILES:
        return jsonify({'error': 'Invalid advisor'}), 400

    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    user['advisor'] = advisor
    add_notification(user, f"🎭 Advisor updated: {ADVISOR_PROFILES[advisor]['name']}", 'info')
    maybe_add_helper_notifications(user)
    save_users(users)

    return jsonify({'success': True, 'advisor': advisor, 'profile': ADVISOR_PROFILES[advisor]})

@bp.route('/api/notifications')
def get_notifications():
    user_id = session.get('player_id')
    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)
    maybe_add_helper_notifications(user)
    unread = sum(1 for n in user['notifications'] if not n.get('read'))
    save_users(users)
    return jsonify({'notifications': list(reversed(user['notifications'])), 'unread': unread})

@bp.route('/api/notifications/read', methods=['POST'])
def mark_notification_read():
    user_id = session.get('player_id')
    data = request.json or {}
    notification_id = data.get('id')
    read_all = bool(data.get('all', False))

    users = load_users()
    user = users[user_id]
    ensure_runtime_fields(user)

    if read_all:
        for notification in user['notifications']:
            notification['read'] = True
    else:
        if notification_id is None:
            return jsonify({'error': 'id required (or all=true)'}), 400
        for notification in user['notifications']:
            if notification.get('id') == notification_id:
                notification['read'] = True
                break

    save_users(users)
    return jsonify({'success': True})

# ==================== LEADERBOARD ====================

@bp.route('/api/leaderboard')
def get_leaderboard():
    users = load_users()
    
    leaderboard = []
    for user_id, user in users.items():
        total_worth = (
            user.get('checking', 0) +
            user.get('savings', 0) +
            user.get('pockets', 0) +
            user.get('emergency', 0)
        )
        
        leaderboard.append({
            'username': user_id,
            'total_worth': total_worth
        })
    
    leaderboard.sort(key=lambda x: x['total_worth'], reverse=True)
    
    return jsonify({'leaderboard': leaderboard[:10]})

# ==================== FRIENDS ====================

@bp.route('/api/friends')
def get_friends():
    user_id = session.get('player_id')
    user = ensure_user(user_id)

    users = load_users()
    me_code = users.get(user_id, {}).get('friend_code')
    
    friends = user.get('friends', [])
    friend_requests = user.get('friendRequests', [])

    friends_payload = []
    for fid in friends:
        friends_payload.append({
            'username': fid,
            'friend_code': users.get(fid, {}).get('friend_code')
        })

    requests_payload = []
    for req in friend_requests:
        from_uid = req.get('from')
        if not from_uid:
            continue
        requests_payload.append({
            'from': from_uid,
            'from_display': req.get('from_display') or from_uid,
            'from_code': users.get(from_uid, {}).get('friend_code')
        })

    return jsonify({
        'me': {'username': user_id, 'friend_code': me_code},
        'friends': friends_payload,
        'requests': requests_payload
    })

@bp.route('/api/friends/send', methods=['POST'])
def send_friend_request():
    user_id = session.get('player_id')
    data = request.get_json(silent=True) or {}
    target_id = (data.get('target') or data.get('target_id') or '').strip()
    
    if not target_id:
        return jsonify({'error': 'Username or 6-digit ID required'}), 400
    
    users = load_users()
    
    target_user_id = resolve_user_identifier(users, target_id)
    
    if not target_user_id:
        return jsonify({'error': 'User not found'}), 404
    
    if target_user_id == user_id:
        return jsonify({'error': 'Cannot add yourself as friend'}), 400
    
    user = users[user_id]
    target_user = users[target_user_id]
    
    # Check if already friends
    if target_user_id in user.get('friends', []):
        return jsonify({'error': 'Already friends'}), 400
    
    # Check if request already sent
    if user_id in [req.get('from') for req in target_user.get('friendRequests', [])]:
        return jsonify({'error': 'Request already sent'}), 400
    
    # Add friend request to target user
    if 'friendRequests' not in target_user:
        target_user['friendRequests'] = []
    
    target_user['friendRequests'].append({
        'from': user_id,
        'from_display': user_id,
        'from_code': users.get(user_id, {}).get('friend_code')
    })
    
    add_notification(target_user, f'👥 Friend request from {user_id}', 'info')
    save_users(users)
    
    return jsonify({'success': True, 'message': 'Friend request sent!'})

@bp.route('/api/friends/accept', methods=['POST'])
def accept_friend_request():
    user_id = session.get('player_id')
    data = request.get_json(silent=True) or {}
    from_id = data.get('from_id')
    
    if not from_id:
        return jsonify({'error': 'Invalid request'}), 400
    
    users = load_users()
    user = users[user_id]
    
    # Find and remove the request
    requests = user.get('friendRequests', [])
    request_found = False
    for req in requests[:]:
        if req.get('from') == from_id:
            requests.remove(req)
            request_found = True
            break
    
    if not request_found:
        return jsonify({'error': 'Request not found'}), 404
    
    # Add to both users' friend lists
    if 'friends' not in user:
        user['friends'] = []
    if 'friends' not in users[from_id]:
        users[from_id]['friends'] = []
    
    user['friends'].append(from_id)
    users[from_id]['friends'].append(user_id)
    
    add_notification(user, f'✅ You are now friends with {from_id}', 'success')
    add_notification(users[from_id], f'✅ {user_id} accepted your friend request!', 'success')
    
    save_users(users)
    
    return jsonify({'success': True, 'message': 'Friend request accepted!'})

@bp.route('/api/friends/remove', methods=['POST'])
def remove_friend():
    user_id = session.get('player_id')
    data = request.get_json(silent=True) or {}
    friend_id = data.get('friend_id')
    
    if not friend_id:
        return jsonify({'error': 'Invalid request'}), 400
    
    users = load_users()
    user = users[user_id]
    
    friends = user.get('friends', [])
    if friend_id not in friends:
        return jsonify({'error': 'Not friends'}), 400
    
    # Remove from both users
    user['friends'].remove(friend_id)
    if friend_id in users and user_id in users[friend_id].get('friends', []):
        users[friend_id]['friends'].remove(user_id)
    
    save_users(users)
    
    return jsonify({'success': True, 'message': 'Friend removed'})


@bp.route('/api/users/lookup', methods=['GET', 'POST'])
def user_lookup():
    """Lookup a user's 6-digit friend code by username (or resolve code back to username)."""
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        username = (data.get('username') or '').strip()
        code = (data.get('friend_code') or data.get('code') or '').strip()
    else:
        username = (request.args.get('username') or '').strip()
        code = (request.args.get('friend_code') or request.args.get('code') or '').strip()

    users = load_users()

    if username:
        uid = username.lower()
        if uid not in users:
            return jsonify({'error': 'User not found'}), 404
        ensure_user(uid)
        users = load_users()
        return jsonify({'username': uid, 'friend_code': users[uid].get('friend_code')})

    if code:
        uid = resolve_user_identifier(users, code)
        if not uid:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'username': uid, 'friend_code': users.get(uid, {}).get('friend_code')})

    return jsonify({'error': 'username or code required'}), 400


@bp.route('/api/feedback', methods=['POST'])
def submit_feedback():
    user_id = session.get('player_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json(silent=True) or {}
    message = str(data.get('message') or '').strip()
    rating_raw = data.get('rating', None)

    if not message:
        return jsonify({'error': 'message is required'}), 400

    rating = None
    if rating_raw is not None and str(rating_raw).strip() != '':
        try:
            rating = int(rating_raw)
        except Exception:
            return jsonify({'error': 'rating must be an integer 1-10'}), 400

        if rating < 1 or rating > 10:
            return jsonify({'error': 'rating must be between 1 and 10'}), 400

    existing = load_json(FEEDBACK_FILE, [])
    if isinstance(existing, dict):
        existing = existing.get('items', []) if isinstance(existing.get('items', None), list) else []
    if not isinstance(existing, list):
        existing = []

    entry = {
        'id': secrets.token_hex(8),
        'user': user_id,
        'rating': rating,
        'message': message,
        'createdAt': datetime.now().isoformat()
    }
    existing.append(entry)

    # Keep file from growing forever.
    existing = existing[-1000:]
    save_json(FEEDBACK_FILE, existing)

    return jsonify({'success': True})

# ==================== HOURLY PROCESSING ====================

def check_and_process_updates():
    """Check if 5 minutes has passed for stock/crypto updates, 1 hour for other updates"""
    config = load_config()
    last_stock_update = config.get('lastStockUpdate')
    last_hourly_update = config.get('lastHourlyUpdate')
    
    now = datetime.now()
    
    # Stock/Crypto updates every 5 minutes
    if last_stock_update is None:
        process_stock_updates(source='auto')
    else:
        try:
            last_update_time = datetime.fromisoformat(last_stock_update)
            minutes_passed = (now - last_update_time).total_seconds() / 60
            if minutes_passed >= 5:
                process_stock_updates(source='auto')
        except Exception as e:
            print(f"[AUTO-STOCK-UPDATE] Error checking last update: {e}")
    
    # Other updates (business, interest, etc.) every 1 hour
    if last_hourly_update is None:
        process_hourly_updates(source='auto')
        return True
    
    try:
        last_update_time = datetime.fromisoformat(last_hourly_update)
        hours_passed = (now - last_update_time).total_seconds() / 3600
        
        if hours_passed >= 1:
            process_hourly_updates(source='auto')
            return True
    except Exception as e:
        print(f"[AUTO-UPDATE] Error checking last update: {e}")
    
    return False

# ==================== ACHIEVEMENT SYSTEM ====================

ACHIEVEMENTS_FILE = Path('game_data/achievements.json')

def load_achievements_config():
    """Load achievement definitions"""
    try:
        with open(ACHIEVEMENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def check_and_unlock_achievement(username, achievement_id):
    """Check if user unlocked an achievement and award it"""
    users = load_users()
    if username not in users:
        return None
    
    user = users[username]
    
    # Initialize achievement tracking
    if 'achievements' not in user:
        user['achievements'] = {
            'unlocked': [],
            'stats': {
                'regular_jobs': 0,
                'gov_jobs': 0,
                'total_jobs': 0,
                'successful_robberies': 0,
                'times_caught': 0,
                'crime_streak': 0,
                'stock_profit': 0,
                'crypto_profit': 0,
                'friends': 0,
                'money_given': 0,
                'recovered_from_debt': False,
                'first_login': True
            }
        }
    
    # Check if already unlocked
    if achievement_id in user['achievements']['unlocked']:
        return None
    
    # Load achievement config
    all_achievements = load_achievements_config()
    achievement = None
    
    # Find the achievement
    for category in all_achievements.values():
        for ach in category:
            if ach['id'] == achievement_id:
                achievement = ach
                break
        if achievement:
            break
    
    if not achievement:
        return None
    
    # Check if requirement met
    stats = user['achievements']['stats']
    req_type = achievement['type']
    requirement = achievement['requirement']
    
    is_unlocked = False
    
    if req_type == 'balance':
        total_balance = user.get('pockets', 0) + user.get('checking', 0) + user.get('savings', 0) + user.get('emergency', 0)
        is_unlocked = total_balance >= requirement
    elif req_type in stats:
        is_unlocked = stats[req_type] >= requirement
    
    if is_unlocked:
        # Unlock achievement
        user['achievements']['unlocked'].append(achievement_id)
        
        # Give reward
        reward = achievement.get('reward', 0)
        user['pockets'] = user.get('pockets', 0) + reward
        
        # Add notification
        if 'notifications' not in user:
            user['notifications'] = []
        
        notif_id = max([n.get('id', 0) for n in user['notifications']], default=0) + 1
        user['notifications'].insert(0, {
            'id': notif_id,
            'message': f"🏆 Achievement Unlocked: {achievement['icon']} {achievement['name']}! +${reward:,}",
            'level': 'success',
            'read': False,
            'createdAt': datetime.now().isoformat()
        })
        
        save_users(users)
        return achievement
    
    return None

def check_all_achievements(username):
    """Check all achievements for a user and unlock any that qualify"""
    all_achievements = load_achievements_config()
    newly_unlocked = []
    
    for category in all_achievements.values():
        for achievement in category:
            result = check_and_unlock_achievement(username, achievement['id'])
            if result:
                newly_unlocked.append(result)
    
    return newly_unlocked

def update_achievement_stat(username, stat_name, value=1, increment=True):
    """Update a user's achievement stat"""
    users = load_users()
    if username not in users:
        return
    
    user = users[username]
    
    if 'achievements' not in user:
        user['achievements'] = {
            'unlocked': [],
            'stats': {}
        }
    
    if 'stats' not in user['achievements']:
        user['achievements']['stats'] = {}
    
    stats = user['achievements']['stats']
    
    if increment:
        stats[stat_name] = stats.get(stat_name, 0) + value
    else:
        stats[stat_name] = value
    
    save_users(users)

@bp.route('/api/achievements', methods=['GET'])
def get_achievements():
    """Get all achievements and user's progress"""
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not logged in'}), 401
    
    users = load_users()
    if username not in users:
        return jsonify({'error': 'User not found'}), 404
    
    user = users[username]
    
    # Initialize if needed
    if 'achievements' not in user:
        user['achievements'] = {
            'unlocked': [],
            'stats': {}
        }
        save_users(users)
    
    # Load all achievement definitions
    all_achievements = load_achievements_config()
    
    # Calculate total balance for wealth achievements
    total_balance = user.get('pockets', 0) + user.get('checking', 0) + user.get('savings', 0) + user.get('emergency', 0)
    
    # Format response with progress
    formatted_achievements = {}
    stats = user['achievements']['stats']
    
    for category, achievements in all_achievements.items():
        formatted_achievements[category] = []
        for ach in achievements:
            is_unlocked = ach['id'] in user['achievements']['unlocked']
            
            # Calculate progress
            progress = 0
            if not is_unlocked:
                if ach['type'] == 'balance':
                    progress = min(100, int((total_balance / ach['requirement']) * 100))
                elif ach['type'] in stats:
                    progress = min(100, int((stats[ach['type']] / ach['requirement']) * 100))
            else:
                progress = 100
            
            formatted_achievements[category].append({
                **ach,
                'unlocked': is_unlocked,
                'progress': progress
            })
    
    return jsonify({
        'achievements': formatted_achievements,
        'stats': stats,
        'total_unlocked': len(user['achievements']['unlocked'])
    })

@bp.route('/api/check_achievements', methods=['POST'])
def check_achievements_endpoint():
    """Manually check for new achievements"""
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not logged in'}), 401
    
    newly_unlocked = check_all_achievements(username)
    
    return jsonify({
        'success': True,
        'newly_unlocked': newly_unlocked
    })

# ==================== CASINO SYSTEM ====================

@bp.route('/api/casino/slots', methods=['POST'])
def play_slots():
    """Play slot machine"""
    user_id = session.get('player_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    bet = int(data.get('bet', 100))
    
    # Validate bet amount
    if bet not in [100, 500, 1000, 5000, 10000]:
        return jsonify({'error': 'Invalid bet amount'}), 400
    
    users = load_users()
    user = users[user_id]
    
    # Check sufficient funds
    if not has_sufficient_funds(user, bet):
        return jsonify({'error': 'Insufficient funds'}), 400
    
    # Deduct bet
    deduct_funds(user, bet)
    
    # Slot symbols with weighted probabilities
    symbols = ['💰', '💎', '🍒', '🔔', '7️⃣', '⭐', '🎰']
    weights = [5, 10, 20, 20, 3, 15, 27]  # Lower weight = rarer
    
    # Spin 3 reels
    reel1 = random.choices(symbols, weights=weights, k=1)[0]
    reel2 = random.choices(symbols, weights=weights, k=1)[0]
    reel3 = random.choices(symbols, weights=weights, k=1)[0]
    
    reels = [reel1, reel2, reel3]
    
    # Calculate payout
    winnings = 0
    message = ''
    
    # Check for jackpot (0.1% chance) - all 7s
    if reel1 == '7️⃣' and reel2 == '7️⃣' and reel3 == '7️⃣':
        winnings = bet * 1000
        message = f'🎉 JACKPOT! 777! Won ${winnings:,}!'
    # All 3 match
    elif reel1 == reel2 == reel3:
        multipliers = {
            '💰': 100,
            '💎': 50,
            '🍒': 25,
            '🔔': 20,
            '⭐': 15,
            '🎰': 10
        }
        multiplier = multipliers.get(reel1, 10)
        winnings = bet * multiplier
        message = f'🎰 Triple Match! {reel1}{reel1}{reel1} Won ${winnings:,}!'
    # 2 match
    elif reel1 == reel2 or reel2 == reel3 or reel1 == reel3:
        winnings = bet * 2
        message = f'👍 Double Match! Won ${winnings:,}'
    else:
        message = f'😞 No match. Lost ${bet:,}'
    
    # Award winnings
    profit = winnings - bet
    if winnings > 0:
        user['pockets'] = user.get('pockets', 0) + winnings
    
    # Track stats
    if 'casino_stats' not in user:
        user['casino_stats'] = {
            'slots_played': 0,
            'slots_wagered': 0,
            'slots_won': 0,
            'biggest_slots_win': 0,
            'blackjack_played': 0,
            'blackjack_wagered': 0,
            'blackjack_won': 0
        }
    
    user['casino_stats']['slots_played'] += 1
    user['casino_stats']['slots_wagered'] += bet
    user['casino_stats']['slots_won'] += profit
    if profit > user['casino_stats']['biggest_slots_win']:
        user['casino_stats']['biggest_slots_win'] = profit
    
    save_users(users)
    
    # Check achievements
    check_all_achievements(user_id)
    
    return jsonify({
        'success': True,
        'reels': reels,
        'winnings': winnings,
        'profit': profit,
        'message': message,
        'balance': user.get('pockets', 0)
    })

@bp.route('/api/casino/blackjack/start', methods=['POST'])
def start_blackjack():
    """Start a new blackjack game"""
    user_id = session.get('player_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    bet = int(data.get('bet', 100))
    
    # Validate bet
    if bet < 100:
        return jsonify({'error': 'Minimum bet is $100'}), 400
    
    users = load_users()
    user = users[user_id]
    
    # Check sufficient funds
    if not has_sufficient_funds(user, bet):
        return jsonify({'error': 'Insufficient funds'}), 400
    
    # Deduct bet
    deduct_funds(user, bet)
    
    # Create deck
    suits = ['♠', '♥', '♦', '♣']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    deck = [{'rank': r, 'suit': s} for s in suits for r in ranks]
    random.shuffle(deck)
    
    # Deal initial cards
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    
    # Calculate hand values
    player_value = calculate_hand_value(player_hand)
    dealer_value = calculate_hand_value([dealer_hand[0]])  # Only show first card
    
    # Store game state in session
    game_state = {
        'deck': deck,
        'player_hand': player_hand,
        'dealer_hand': dealer_hand,
        'bet': bet,
        'game_over': False
    }
    
    # Check for blackjack
    if player_value == 21:
        dealer_total = calculate_hand_value(dealer_hand)
        if dealer_total == 21:
            # Push
            user['pockets'] = user.get('pockets', 0) + bet
            game_state['game_over'] = True
            save_users(users)
            return jsonify({
                'success': True,
                'player_hand': player_hand,
                'dealer_hand': dealer_hand,
                'player_value': player_value,
                'dealer_value': dealer_total,
                'game_over': True,
                'result': 'push',
                'message': '🤝 Push! Both have blackjack.',
                'winnings': 0,
                'balance': user.get('pockets', 0)
            })
        else:
            # Player blackjack - pays 3:2
            winnings = int(bet * 2.5)
            user['pockets'] = user.get('pockets', 0) + winnings
            game_state['game_over'] = True
            save_users(users)
            return jsonify({
                'success': True,
                'player_hand': player_hand,
                'dealer_hand': dealer_hand,
                'player_value': player_value,
                'dealer_value': calculate_hand_value(dealer_hand),
                'game_over': True,
                'result': 'blackjack',
                'message': f'🎉 BLACKJACK! Won ${winnings:,}!',
                'winnings': winnings,
                'balance': user.get('pockets', 0)
            })
    
    session['blackjack_game'] = game_state
    save_users(users)
    
    return jsonify({
        'success': True,
        'player_hand': player_hand,
        'dealer_hand': [dealer_hand[0]],  # Only show first dealer card
        'player_value': player_value,
        'dealer_value': dealer_value,
        'game_over': False
    })

@bp.route('/api/casino/blackjack/hit', methods=['POST'])
def blackjack_hit():
    """Hit in blackjack"""
    user_id = session.get('player_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    
    game_state = session.get('blackjack_game')
    if not game_state or game_state.get('game_over'):
        return jsonify({'error': 'No active game'}), 400
    
    # Draw card
    card = game_state['deck'].pop()
    game_state['player_hand'].append(card)
    
    player_value = calculate_hand_value(game_state['player_hand'])
    
    # Check for bust
    if player_value > 21:
        game_state['game_over'] = True
        session['blackjack_game'] = game_state
        
        return jsonify({
            'success': True,
            'player_hand': game_state['player_hand'],
            'dealer_hand': game_state['dealer_hand'],
            'player_value': player_value,
            'dealer_value': calculate_hand_value(game_state['dealer_hand']),
            'game_over': True,
            'result': 'bust',
            'message': f'💥 Bust! Lost ${game_state["bet"]:,}',
            'winnings': 0,
            'balance': load_users()[user_id].get('pockets', 0)
        })
    
    session['blackjack_game'] = game_state
    
    return jsonify({
        'success': True,
        'player_hand': game_state['player_hand'],
        'dealer_hand': [game_state['dealer_hand'][0]],
        'player_value': player_value,
        'dealer_value': calculate_hand_value([game_state['dealer_hand'][0]]),
        'game_over': False
    })

@bp.route('/api/casino/blackjack/stand', methods=['POST'])
def blackjack_stand():
    """Stand in blackjack - dealer plays"""
    user_id = session.get('player_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    
    game_state = session.get('blackjack_game')
    if not game_state or game_state.get('game_over'):
        return jsonify({'error': 'No active game'}), 400
    
    player_value = calculate_hand_value(game_state['player_hand'])
    
    # Dealer plays - hits on 16, stands on 17
    while calculate_hand_value(game_state['dealer_hand']) < 17:
        game_state['dealer_hand'].append(game_state['deck'].pop())
    
    dealer_value = calculate_hand_value(game_state['dealer_hand'])
    game_state['game_over'] = True
    
    # Determine winner
    users = load_users()
    user = users[user_id]
    bet = game_state['bet']
    
    if dealer_value > 21:
        # Dealer bust - player wins
        winnings = bet * 2
        result = 'win'
        message = f'🎉 Dealer bust! Won ${winnings:,}!'
    elif player_value > dealer_value:
        # Player wins
        winnings = bet * 2
        result = 'win'
        message = f'🎉 You win! Won ${winnings:,}!'
    elif player_value < dealer_value:
        # Dealer wins
        winnings = 0
        result = 'lose'
        message = f'😞 Dealer wins. Lost ${bet:,}'
    else:
        # Push
        winnings = bet
        result = 'push'
        message = '🤝 Push! Bet returned.'
    
    # Award winnings
    user['pockets'] = user.get('pockets', 0) + winnings
    
    # Track stats
    if 'casino_stats' not in user:
        user['casino_stats'] = {
            'slots_played': 0,
            'slots_wagered': 0,
            'slots_won': 0,
            'biggest_slots_win': 0,
            'blackjack_played': 0,
            'blackjack_wagered': 0,
            'blackjack_won': 0
        }
    
    profit = winnings - bet
    user['casino_stats']['blackjack_played'] += 1
    user['casino_stats']['blackjack_wagered'] += bet
    user['casino_stats']['blackjack_won'] += profit
    
    save_users(users)
    session['blackjack_game'] = game_state
    
    # Check achievements
    check_all_achievements(user_id)
    
    return jsonify({
        'success': True,
        'player_hand': game_state['player_hand'],
        'dealer_hand': game_state['dealer_hand'],
        'player_value': player_value,
        'dealer_value': dealer_value,
        'game_over': True,
        'result': result,
        'message': message,
        'winnings': winnings,
        'balance': user.get('pockets', 0)
    })

def calculate_hand_value(hand):
    """Calculate blackjack hand value"""
    value = 0
    aces = 0
    
    for card in hand:
        rank = card['rank']
        if rank in ['J', 'Q', 'K']:
            value += 10
        elif rank == 'A':
            aces += 1
            value += 11
        else:
            value += int(rank)
    
    # Adjust for aces
    while value > 21 and aces > 0:
        value -= 10
        aces -= 1
    
    return value

@bp.route('/api/casino/stats', methods=['GET'])
def get_casino_stats():
    """Get player's casino statistics"""
    user_id = session.get('player_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    
    users = load_users()
    user = users[user_id]
    
    stats = user.get('casino_stats', {
        'slots_played': 0,
        'slots_wagered': 0,
        'slots_won': 0,
        'biggest_slots_win': 0,
        'blackjack_played': 0,
        'blackjack_wagered': 0,
        'blackjack_won': 0
    })
    
    return jsonify(stats)

# ==================== PLAYER TRADING SYSTEM ====================

TRADES_FILE = Path('game_data/trades.json')

def load_trades():
    """Load active trades"""
    if TRADES_FILE.exists():
        with open(TRADES_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_trades(trades):
    """Save trades"""
    with open(TRADES_FILE, 'w') as f:
        json.dump(trades, f, indent=2)

@bp.route('/api/trades/active')
def get_active_trades():
    """Get all active trade requests for current user"""
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not logged in'}), 401
    
    trades = load_trades()
    
    # Filter trades involving this user
    user_trades = {
        'sent': [],      # Trades initiated by user
        'received': []   # Trades sent to user
    }
    
    for trade_id, trade in trades.items():
        if trade['status'] == 'pending':
            if trade['initiator'] == username:
                user_trades['sent'].append(trade)
            elif trade['target'] == username:
                user_trades['received'].append(trade)
    
    return jsonify(user_trades)

@bp.route('/api/trades/history')
def get_trade_history():
    """Get completed trade history for current user"""
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not logged in'}), 401
    
    users = load_users()
    user = users.get(username, {})
    
    history = user.get('trade_history', [])
    
    # Return last 50 trades
    return jsonify({'history': history[-50:]})

@bp.route('/api/trades/create', methods=['POST'])
def create_trade():
    """Create a new trade request"""
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    target_username = data.get('target', '').strip()
    
    # Validate target
    if not target_username:
        return jsonify({'error': 'Target player required'}), 400
    
    users = load_users()
    
    if target_username not in users:
        return jsonify({'error': 'Target player not found'}), 404
    
    if target_username == username:
        return jsonify({'error': 'Cannot trade with yourself'}), 400
    
    user = users[username]
    
    # Parse offer (what initiator is giving)
    offer = {
        'money': int(data.get('offer_money', 0)),
        'items': data.get('offer_items', {}),      # {item_id: quantity}
        'stocks': data.get('offer_stocks', {}),    # {symbol: shares}
        'crypto': data.get('offer_crypto', {})     # {symbol: amount}
    }
    
    # Parse request (what initiator wants)
    request_items = {
        'money': int(data.get('request_money', 0)),
        'items': data.get('request_items', {}),
        'stocks': data.get('request_stocks', {}),
        'crypto': data.get('request_crypto', {})
    }
    
    # Validate initiator has what they're offering
    if offer['money'] > 0:
        total_balance = user.get('pockets', 0) + user.get('checking', 0) + user.get('savings', 0)
        if total_balance < offer['money']:
            return jsonify({'error': 'Insufficient funds'}), 400
    
    for item_id, quantity in offer['items'].items():
        if user.get('inventory', {}).get(item_id, 0) < quantity:
            return jsonify({'error': f'Insufficient item: {item_id}'}), 400
    
    for symbol, shares in offer['stocks'].items():
        if user.get('stocks', {}).get(symbol, 0) < shares:
            return jsonify({'error': f'Insufficient stock: {symbol}'}), 400
    
    for symbol, amount in offer['crypto'].items():
        if user.get('crypto', {}).get(symbol, 0) < amount:
            return jsonify({'error': f'Insufficient crypto: {symbol}'}), 400
    
    # Create trade
    trades = load_trades()
    trade_id = secrets.token_hex(8)
    
    trades[trade_id] = {
        'id': trade_id,
        'initiator': username,
        'target': target_username,
        'offer': offer,
        'request': request_items,
        'status': 'pending',
        'created_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(minutes=30)).isoformat()
    }
    
    save_trades(trades)
    
    # Notify target player
    target = users[target_username]
    add_notification(target, f'💱 Trade request from {username}', 'info')
    save_users(users)
    
    return jsonify({'success': True, 'trade': trades[trade_id]})

@bp.route('/api/trades/accept/<trade_id>', methods=['POST'])
def accept_trade(trade_id):
    """Accept a trade request"""
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not logged in'}), 401
    
    trades = load_trades()
    
    if trade_id not in trades:
        return jsonify({'error': 'Trade not found'}), 404
    
    trade = trades[trade_id]
    
    # Verify user is the target
    if trade['target'] != username:
        return jsonify({'error': 'Not your trade to accept'}), 403
    
    if trade['status'] != 'pending':
        return jsonify({'error': 'Trade already processed'}), 400
    
    # Check if expired
    if datetime.fromisoformat(trade['expires_at']) < datetime.now():
        trade['status'] = 'expired'
        save_trades(trades)
        return jsonify({'error': 'Trade expired'}), 400
    
    users = load_users()
    initiator = users[trade['initiator']]
    target = users[username]
    
    # Verify both parties still have the offered items
    offer = trade['offer']
    request = trade['request']
    
    # Check initiator's offer
    init_balance = initiator.get('pockets', 0) + initiator.get('checking', 0) + initiator.get('savings', 0)
    if init_balance < offer['money']:
        trade['status'] = 'failed'
        save_trades(trades)
        return jsonify({'error': 'Initiator no longer has sufficient funds'}), 400
    
    for item_id, quantity in offer['items'].items():
        if initiator.get('inventory', {}).get(item_id, 0) < quantity:
            trade['status'] = 'failed'
            save_trades(trades)
            return jsonify({'error': f'Initiator no longer has item: {item_id}'}), 400
    
    for symbol, shares in offer['stocks'].items():
        if initiator.get('stocks', {}).get(symbol, 0) < shares:
            trade['status'] = 'failed'
            save_trades(trades)
            return jsonify({'error': f'Initiator no longer has stock: {symbol}'}), 400
    
    for symbol, amount in offer['crypto'].items():
        if initiator.get('crypto', {}).get(symbol, 0) < amount:
            trade['status'] = 'failed'
            save_trades(trades)
            return jsonify({'error': f'Initiator no longer has crypto: {symbol}'}), 400
    
    # Check target's request
    target_balance = target.get('pockets', 0) + target.get('checking', 0) + target.get('savings', 0)
    if target_balance < request['money']:
        trade['status'] = 'failed'
        save_trades(trades)
        return jsonify({'error': 'You no longer have sufficient funds'}), 400
    
    for item_id, quantity in request['items'].items():
        if target.get('inventory', {}).get(item_id, 0) < quantity:
            trade['status'] = 'failed'
            save_trades(trades)
            return jsonify({'error': f'You no longer have item: {item_id}'}), 400
    
    for symbol, shares in request['stocks'].items():
        if target.get('stocks', {}).get(symbol, 0) < shares:
            trade['status'] = 'failed'
            save_trades(trades)
            return jsonify({'error': f'You no longer have stock: {symbol}'}), 400
    
    for symbol, amount in request['crypto'].items():
        if target.get('crypto', {}).get(symbol, 0) < amount:
            trade['status'] = 'failed'
            save_trades(trades)
            return jsonify({'error': f'You no longer have crypto: {symbol}'}), 400
    
    # Execute trade - transfer assets
    # Initiator gives offer, receives request
    if offer['money'] > 0:
        deduct_funds(initiator, offer['money'])
        target['pockets'] = target.get('pockets', 0) + offer['money']
    
    if request['money'] > 0:
        deduct_funds(target, request['money'])
        initiator['pockets'] = initiator.get('pockets', 0) + request['money']
    
    # Transfer items
    for item_id, quantity in offer['items'].items():
        initiator['inventory'][item_id] = initiator.get('inventory', {}).get(item_id, 0) - quantity
        if initiator['inventory'][item_id] <= 0:
            del initiator['inventory'][item_id]
        target['inventory'][item_id] = target.get('inventory', {}).get(item_id, 0) + quantity
    
    for item_id, quantity in request['items'].items():
        target['inventory'][item_id] = target.get('inventory', {}).get(item_id, 0) - quantity
        if target['inventory'][item_id] <= 0:
            del target['inventory'][item_id]
        initiator['inventory'][item_id] = initiator.get('inventory', {}).get(item_id, 0) + quantity
    
    # Transfer stocks
    for symbol, shares in offer['stocks'].items():
        initiator['stocks'][symbol] = initiator.get('stocks', {}).get(symbol, 0) - shares
        if initiator['stocks'][symbol] <= 0:
            del initiator['stocks'][symbol]
        target['stocks'][symbol] = target.get('stocks', {}).get(symbol, 0) + shares
    
    for symbol, shares in request['stocks'].items():
        target['stocks'][symbol] = target.get('stocks', {}).get(symbol, 0) - shares
        if target['stocks'][symbol] <= 0:
            del target['stocks'][symbol]
        initiator['stocks'][symbol] = initiator.get('stocks', {}).get(symbol, 0) + shares
    
    # Transfer crypto
    for symbol, amount in offer['crypto'].items():
        initiator['crypto'][symbol] = initiator.get('crypto', {}).get(symbol, 0) - amount
        if initiator['crypto'][symbol] <= 0:
            del initiator['crypto'][symbol]
        target['crypto'][symbol] = target.get('crypto', {}).get(symbol, 0) + amount
    
    for symbol, amount in request['crypto'].items():
        target['crypto'][symbol] = target.get('crypto', {}).get(symbol, 0) - amount
        if target['crypto'][symbol] <= 0:
            del target['crypto'][symbol]
        initiator['crypto'][symbol] = initiator.get('crypto', {}).get(symbol, 0) + amount
    
    # Update trade status
    trade['status'] = 'completed'
    trade['completed_at'] = datetime.now().isoformat()
    
    # Add to trade history for both users
    if 'trade_history' not in initiator:
        initiator['trade_history'] = []
    if 'trade_history' not in target:
        target['trade_history'] = []
    
    trade_record = {
        'trade_id': trade_id,
        'partner': trade['target'] if username == trade['initiator'] else trade['initiator'],
        'gave': offer if username == trade['initiator'] else request,
        'received': request if username == trade['initiator'] else offer,
        'completed_at': trade['completed_at']
    }
    
    initiator['trade_history'].append({**trade_record, 'partner': trade['target']})
    target['trade_history'].append({**trade_record, 'partner': trade['initiator']})
    
    # Notifications
    add_notification(initiator, f'✅ Trade with {username} completed!', 'success')
    add_notification(target, f'✅ Trade with {trade["initiator"]} completed!', 'success')
    
    # Update achievement stats
    update_achievement_stat(trade['initiator'], 'trades_completed', 1)
    update_achievement_stat(username, 'trades_completed', 1)
    
    save_trades(trades)
    save_users(users)
    
    return jsonify({'success': True, 'message': 'Trade completed!'})

@bp.route('/api/trades/decline/<trade_id>', methods=['POST'])
def decline_trade(trade_id):
    """Decline a trade request"""
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not logged in'}), 401
    
    trades = load_trades()
    
    if trade_id not in trades:
        return jsonify({'error': 'Trade not found'}), 404
    
    trade = trades[trade_id]
    
    # Verify user is the target
    if trade['target'] != username:
        return jsonify({'error': 'Not your trade to decline'}), 403
    
    if trade['status'] != 'pending':
        return jsonify({'error': 'Trade already processed'}), 400
    
    trade['status'] = 'declined'
    trade['declined_at'] = datetime.now().isoformat()
    
    save_trades(trades)
    
    # Notify initiator
    users = load_users()
    if trade['initiator'] in users:
        initiator = users[trade['initiator']]
        add_notification(initiator, f'❌ {username} declined your trade request', 'warning')
        save_users(users)
    
    return jsonify({'success': True, 'message': 'Trade declined'})

@bp.route('/api/trades/cancel/<trade_id>', methods=['POST'])
def cancel_trade(trade_id):
    """Cancel your own trade request"""
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not logged in'}), 401
    
    trades = load_trades()
    
    if trade_id not in trades:
        return jsonify({'error': 'Trade not found'}), 404
    
    trade = trades[trade_id]
    
    # Verify user is the initiator
    if trade['initiator'] != username:
        return jsonify({'error': 'Not your trade to cancel'}), 403
    
    if trade['status'] != 'pending':
        return jsonify({'error': 'Trade already processed'}), 400
    
    trade['status'] = 'cancelled'
    trade['cancelled_at'] = datetime.now().isoformat()
    
    save_trades(trades)
    
    return jsonify({'success': True, 'message': 'Trade cancelled'})

# ==================== HOURLY UPDATES ====================
def process_stock_updates(source: str = 'auto'):
    """Process stock and crypto price updates (every 5 minutes)."""
    started_at = datetime.now()
    config = load_config()
    previous_last = config.get('lastStockUpdate')
    stats = {
        'stocks_updated': 0,
        'crypto_updated': 0,
    }
    ok = True
    error_message = None
    
    try:
        # Update stock prices
        stocks = load_stocks()
        for symbol, stock in stocks.items():
            old_price = stock['price']
            change_percent = random.uniform(-0.05, 0.05)  # -5% to +5%
            if config.get('recession', False):
                change_percent -= 0.02  # Extra -2% during recession

            stock['price'] = max(1, int(stock['price'] * (1 + change_percent)))
            price_change = stock['price'] - old_price
            stock['change_points'] = price_change  # Track point change
            
            if 'history' not in stock:
                stock['history'] = []
            stock['history'].append({
                'time': datetime.now().isoformat(),
                'price': stock['price']
            })
            # Keep only last 100 history points
            stock['history'] = stock['history'][-100:]
        stats['stocks_updated'] = len(stocks)
        save_stocks(stocks)

        # Update crypto prices
        crypto = load_crypto()
        for symbol, coin in crypto.items():
            old_price = coin['price']
            change_percent = random.uniform(-0.1, 0.1)  # -10% to +10% (more volatile)
            coin['price'] = max(0.01, coin['price'] * (1 + change_percent))
            price_change = coin['price'] - old_price
            coin['change_points'] = round(price_change, 2)  # Track point change

            if 'history' not in coin:
                coin['history'] = []
            coin['history'].append({
                'time': datetime.now().isoformat(),
                'price': coin['price']
            })
            coin['history'] = coin['history'][-100:]
        stats['crypto_updated'] = len(crypto)
        save_crypto(crypto)

        config['lastStockUpdate'] = datetime.now().isoformat()
        save_config(config)

        print(f"[STOCK-UPDATE] ({source}) Processed {stats['stocks_updated']} stocks, {stats['crypto_updated']} crypto at {datetime.now()}")
    except Exception as e:
        ok = False
        error_message = str(e)
        print(f"[STOCK-UPDATE] ({source}) Error processing updates: {e}")
    finally:
        finished_at = datetime.now()
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        entry = {
            'id': secrets.token_hex(8),
            'timestamp': started_at.isoformat(),
            'source': (source or 'auto'),
            'type': 'stock_update',
            'ok': ok,
            'duration_ms': duration_ms,
            'previous_lastStockUpdate': previous_last,
            'new_lastStockUpdate': config.get('lastStockUpdate'),
            **stats,
        }
        if error_message:
            entry['error'] = error_message
        append_hourly_log(entry)

def process_hourly_updates(source: str = 'auto'):
    """Process all hourly game updates (businesses, loans, interest)."""
    started_at = datetime.now()
    config = load_config()
    previous_last = config.get('lastHourlyUpdate')
    stats = {
        'businesses_processed': 0,
        'users_processed': 0,
    }
    ok = True
    error_message = None
    
    try:
        # Process business stats (business-level ops now drive revenue/profit)
        businesses = load_businesses()
        users = load_users()
        for business_id, business in businesses.items():
            if not isinstance(business, dict):
                continue
            init_business_structure(business)
            owner_id = business.get('owner')
            owner = users.get(owner_id, {}) if isinstance(users, dict) else {}
            if isinstance(owner, dict):
                ensure_runtime_fields(owner)
            snap = _business_ops_snapshot(business, owner_user=owner)
            business['revenue'] = int(snap.get('net_per_hour', 0))
            business['dailyRevenue'] = int(snap.get('net_per_day', 0))
        stats['businesses_processed'] = len(businesses)
        save_businesses(businesses)

        # Process interest on loans
        for user_id, user in users.items():
            loans = user.get('loans', {})

            for loan_type, loan in loans.items():
                if loan.get('currentDebt', 0) > 0:
                    interest_rate = config.get('interestRate', 3) / 100
                    daily_interest = loan['currentDebt'] * (interest_rate / 24)  # Hourly
                    loan['currentDebt'] = int(loan['currentDebt'] + daily_interest)

            # Process savings interest
            savings = user.get('savings', 0)
            if savings > 0:
                interest_rate = config.get('interestRate', 3) / 100
                hourly_interest = savings * (interest_rate / 24 / 365)
                user['savings'] = int(savings + hourly_interest)

        stats['users_processed'] = len(users)
        save_users(users)

        config['lastHourlyUpdate'] = datetime.now().isoformat()
        save_config(config)

        print(f"[HOURLY] ({source}) Processed updates at {datetime.now()}")
    except Exception as e:
        ok = False
        error_message = str(e)
        print(f"[HOURLY] ({source}) Error processing updates: {e}")
    finally:
        finished_at = datetime.now()
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        entry = {
            'id': secrets.token_hex(8),
            'timestamp': started_at.isoformat(),
            'source': (source or 'auto'),
            'ok': ok,
            'duration_ms': duration_ms,
            'previous_lastHourlyUpdate': previous_last,
            'new_lastHourlyUpdate': config.get('lastHourlyUpdate'),
            **stats,
        }
        if error_message:
            entry['error'] = error_message
        append_hourly_log(entry)

# You can set up a background task or cron job to call process_hourly_updates()
# For now, we'll add a manual endpoint
@bp.route('/api/process_hourly', methods=['POST'])
def trigger_hourly():
    process_hourly_updates(source='manual')
    return jsonify({'success': True, 'message': 'Hourly updates processed'})

# ==================== BUSINESS MODE (AI EMPLOYEES & UPGRADES) ====================

# AI Employee roles and skill levels
AI_EMPLOYEE_ROLES = ['Marketing', 'Operations', 'Finance', 'Tech']

AI_EMPLOYEE_SKILLS = {
    'novice': {'cost': 50000, 'multiplier': 1.0},
    'intermediate': {'cost': 100000, 'multiplier': 1.3},
    'advanced': {'cost': 200000, 'multiplier': 1.6},
    'professional': {'cost': 350000, 'multiplier': 2.0},
    'expert': {'cost': 500000, 'multiplier': 2.5}
}

# Business upgrade categories and tiers
BUSINESS_UPGRADES = {
    'automation': {
        'name': 'Automation',
        'description': 'Increase operational efficiency',
        'tiers': [
            {'level': 1, 'cost': 100000, 'effect': 0.20, 'name': 'Basic Automation'},
            {'level': 2, 'cost': 500000, 'effect': 0.35, 'name': 'Advanced Automation'},
            {'level': 3, 'cost': 2000000, 'effect': 0.50, 'name': 'Full Automation'}
        ]
    },
    'marketing': {
        'name': 'Marketing',
        'description': 'Expand customer reach',
        'tiers': [
            {'level': 1, 'cost': 150000, 'effect': 0.15, 'name': 'Social Media'},
            {'level': 2, 'cost': 750000, 'effect': 0.25, 'name': 'Digital Campaigns'},
            {'level': 3, 'cost': 3000000, 'effect': 0.40, 'name': 'Global Marketing'}
        ]
    },
    'infrastructure': {
        'name': 'Infrastructure',
        'description': 'Improve business capacity',
        'tiers': [
            {'level': 1, 'cost': 200000, 'effect': 0.25, 'name': 'Cloud Systems'},
            {'level': 2, 'cost': 1000000, 'effect': 0.40, 'name': 'Data Centers'},
            {'level': 3, 'cost': 4000000, 'effect': 0.60, 'name': 'Enterprise Infrastructure'}
        ]
    },
    'research': {
        'name': 'Research & Development',
        'description': 'Drive innovation',
        'tiers': [
            {'level': 1, 'cost': 100000, 'effect': 0.10, 'name': 'R&D Lab'},
            {'level': 2, 'cost': 500000, 'effect': 0.20, 'name': 'Innovation Center'},
            {'level': 3, 'cost': 2000000, 'effect': 0.35, 'name': 'Advanced R&D'}
        ]
    },
    'expansion': {
        'name': 'Expansion',
        'description': 'Increase market presence',
        'tiers': [
            {'level': 1, 'cost': 250000, 'effect': 0.30, 'name': 'Regional Expansion'},
            {'level': 2, 'cost': 1250000, 'effect': 0.50, 'name': 'National Expansion'},
            {'level': 3, 'cost': 5000000, 'effect': 0.75, 'name': 'Global Expansion'}
        ]
    }
}

def init_business_mode(user, business_id=None):
    """Initialize business mode structure for user.

    New format: user['business_mode'] is a mapping of business_id -> business_mode_data.
    Legacy single-object format will be migrated under the key '__default__'.
    If business_id is None, use '__default__' to preserve backward compatibility.
    """
    # Ensure top-level map exists and migrate legacy format if needed
    if 'business_mode' in user and isinstance(user['business_mode'], dict):
        # If it looks like the legacy single-object format (has 'employees' key), migrate
        if any(k in user['business_mode'] for k in ('employees', 'upgrades', 'total_revenue', 'last_collection')):
            legacy = user['business_mode']
            user['business_mode'] = {'__default__': legacy}
    elif 'business_mode' not in user:
        user['business_mode'] = {}

    key = '__default__' if not business_id else str(business_id)

    if key not in user['business_mode']:
        user['business_mode'][key] = {
            'employees': [],
            'upgrades': {},
            'total_revenue': 0,
            'last_collection': datetime.now().isoformat()
        }

    return user['business_mode'][key]

def calculate_business_revenue(business_mode):
    """Calculate accumulated revenue based on employees and upgrades"""
    if not business_mode.get('employees'):
        return 0
    
    # Base revenue per hour
    base_revenue = 1000
    
    # Calculate employee multiplier
    employee_count = len(business_mode['employees'])
    employee_multiplier = 0
    
    for employee in business_mode['employees']:
        skill = employee.get('skill', 'novice')
        employee_multiplier += AI_EMPLOYEE_SKILLS[skill]['multiplier']
    
    # Total employee contribution
    employee_factor = 1 + (0.5 * employee_count) + employee_multiplier
    
    # Calculate upgrade multipliers
    upgrade_multiplier = 1.0
    for category, tier in business_mode.get('upgrades', {}).items():
        if category in BUSINESS_UPGRADES and tier > 0:
            tier_index = tier - 1
            if tier_index < len(BUSINESS_UPGRADES[category]['tiers']):
                upgrade_multiplier += BUSINESS_UPGRADES[category]['tiers'][tier_index]['effect']
    
    # Calculate time elapsed
    last_collection = datetime.fromisoformat(business_mode.get('last_collection', datetime.now().isoformat()))
    hours_elapsed = (datetime.now() - last_collection).total_seconds() / 3600
    
    # Total revenue
    total_revenue = base_revenue * employee_factor * upgrade_multiplier * hours_elapsed
    
    return int(total_revenue)

@bp.route('/api/business_mode/status')
def business_mode_status():
    """Get current business mode status"""
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not logged in'}), 401
    
    users = load_users()
    user_id = session.get('player_id')
    user = users[user_id]
    
    ensure_runtime_fields(user)

    # Optional business_id query parameter to scope Business Mode to a specific business
    business_id = request.args.get('business_id') if request.args else None

    # Business-level operations (preferred): if a business_id is provided, operate on the business object.
    if business_id:
        businesses = load_businesses()
        biz = businesses.get(str(business_id)) if isinstance(businesses, dict) else None
        if not isinstance(biz, dict):
            return jsonify({'error': 'Business not found'}), 404

        init_business_structure(biz)
        if biz.get('owner') != user_id:
            return jsonify({'error': 'Not your business'}), 403

        snap = _business_ops_snapshot(biz, owner_user=user)

        # Available hires if capacity allows
        available_hires = []
        if snap.get('employee_count', 0) < snap.get('max_employees', 2):
            for emp_type, info in EMPLOYEE_TYPES.items():
                available_hires.append({
                    'type': emp_type,
                    'name': emp_type.replace('_', ' ').title(),
                    'cost': _coerce_int_amount(info.get('cost', 0)),
                    'salary_per_day': _coerce_int_amount(info.get('salary', 0)),
                    'revenue_per_day': _coerce_int_amount(info.get('revenue', 0)),
                })

        # Available upgrades: next tier per category
        available_upgrades = []
        current_upgrades = biz.get('upgrades', {}) if isinstance(biz.get('upgrades', {}), dict) else {}
        for category, tiers in UPGRADE_TIERS.items():
            current_tier = _coerce_int_amount(current_upgrades.get(category, 0))
            if current_tier < len(tiers):
                next_tier = tiers[current_tier]
                payload = {
                    'category': category,
                    'name': category.replace('_', ' ').title(),
                    'tier': _coerce_int_amount(next_tier.get('level', current_tier + 1)),
                    'tier_name': next_tier.get('name', f'Tier {current_tier + 1}'),
                    'cost': _coerce_int_amount(next_tier.get('cost', 0)),
                }
                # Effect labels (UI-friendly)
                if 'bonus' in next_tier:
                    payload['effect'] = float(next_tier.get('bonus', 0))
                    payload['effect_label'] = f"+{int(float(next_tier.get('bonus', 0)) * 100)}%"
                elif 'traffic' in next_tier:
                    payload['effect'] = float(next_tier.get('traffic', 1.0))
                    payload['effect_label'] = f"x{float(next_tier.get('traffic', 1.0))} traffic"
                elif 'capacity' in next_tier:
                    payload['effect'] = _coerce_int_amount(next_tier.get('capacity', 0))
                    payload['effect_label'] = f"{_coerce_int_amount(next_tier.get('capacity', 0))} customers/day"
                available_upgrades.append(payload)

        return jsonify({
            'mode': 'business',
            'business_id': str(business_id),
            'employees': snap.get('employees_normalized', []),
            'upgrades': current_upgrades,
            'max_employees': snap.get('max_employees', 2),
            'gross_per_day': snap.get('gross_per_day', 0),
            'salary_per_day': snap.get('salary_per_day', 0),
            'tax_rate': snap.get('tax_rate', 0.0),
            'tax_rate_percent': round(float(snap.get('tax_rate', 0.0)) * 100.0, 2),
            'tax_per_day': snap.get('tax_per_day', 0),
            'accumulated_gross': snap.get('accumulated_gross', 0),
            'accumulated_salary': snap.get('accumulated_salary', 0),
            'accumulated_tax': snap.get('accumulated_tax', 0),
            'total_revenue': _coerce_int_amount(biz.get('totalEarnings', 0)),
            'accumulated_revenue': snap.get('accumulated_profit', 0),
            'revenue_rate': snap.get('net_per_hour', 0),
            'available_hires': available_hires,
            'available_upgrades': available_upgrades,
        })

    business_mode = init_business_mode(user, business_id)

    # Calculate current revenue
    accumulated_revenue = calculate_business_revenue(business_mode)
    
    # Calculate revenue rate (per hour)
    revenue_rate = 0
    if business_mode.get('employees'):
        base_revenue = 1000
        employee_count = len(business_mode['employees'])
        employee_multiplier = sum(AI_EMPLOYEE_SKILLS[emp['skill']]['multiplier'] 
                                 for emp in business_mode['employees'])
        employee_factor = 1 + (0.5 * employee_count) + employee_multiplier
        
        upgrade_multiplier = 1.0
        for category, tier in business_mode.get('upgrades', {}).items():
            if category in BUSINESS_UPGRADES and tier > 0:
                tier_index = tier - 1
                if tier_index < len(BUSINESS_UPGRADES[category]['tiers']):
                    upgrade_multiplier += BUSINESS_UPGRADES[category]['tiers'][tier_index]['effect']
        
        revenue_rate = int(base_revenue * employee_factor * upgrade_multiplier)
    
    # Get available hires (not yet hired)
    hired_employees = {(emp['role'], emp['skill']) for emp in business_mode['employees']}
    available_hires = []
    
    for role in AI_EMPLOYEE_ROLES:
        for skill, details in AI_EMPLOYEE_SKILLS.items():
            if (role, skill) not in hired_employees:
                available_hires.append({
                    'role': role,
                    'skill': skill,
                    'cost': details['cost'],
                    'multiplier': details['multiplier']
                })
    
    # Get available upgrades
    available_upgrades = []
    current_upgrades = business_mode.get('upgrades', {})
    
    for category, upgrade in BUSINESS_UPGRADES.items():
        current_tier = current_upgrades.get(category, 0)
        for tier in upgrade['tiers']:
            if tier['level'] == current_tier + 1:  # Next tier
                available_upgrades.append({
                    'category': category,
                    'name': upgrade['name'],
                    'description': upgrade['description'],
                    'tier': tier['level'],
                    'tier_name': tier['name'],
                    'cost': tier['cost'],
                    'effect': tier['effect']
                })
                break
    
    return jsonify({
        'employees': business_mode['employees'],
        'upgrades': business_mode.get('upgrades', {}),
        'total_revenue': business_mode['total_revenue'],
        'accumulated_revenue': accumulated_revenue,
        'revenue_rate': revenue_rate,
        'available_hires': available_hires,
        'available_upgrades': available_upgrades
    })

@bp.route('/api/business_mode/hire', methods=['POST'])
def hire_ai_employee():
    """Hire an AI employee"""
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json(silent=True) or {}

    # If a business_id is provided, use the business-level employee system.
    business_id = data.get('business_id')
    if business_id:
        employee_type = (
            data.get('employee_type')
            or data.get('employeeType')
            or data.get('type')
            or (data.get('role') if not data.get('skill') else None)
        )
        employee_type = (str(employee_type).strip().lower() if employee_type else '')
        if employee_type not in EMPLOYEE_TYPES:
            return jsonify({'error': 'Invalid employee type'}), 400

        users = load_users()
        user_id = session.get('player_id')
        user = users[user_id]
        ensure_runtime_fields(user)

        businesses = load_businesses()
        biz = businesses.get(str(business_id)) if isinstance(businesses, dict) else None
        if not isinstance(biz, dict):
            return jsonify({'error': 'Business not found'}), 404
        init_business_structure(biz)
        if biz.get('owner') != user_id:
            return jsonify({'error': 'Not your business'}), 403

        # Capacity check
        cap = _business_ops_employee_cap(biz)
        current = biz.get('employees', []) if isinstance(biz.get('employees', []), list) else []
        if len(current) >= cap:
            return jsonify({'error': f'Employee capacity reached ({cap}). Upgrade Capacity to hire more.'}), 400

        base_cost = _coerce_int_amount(EMPLOYEE_TYPES[employee_type].get('cost', 0))
        advisor = get_advisor(user)
        cost = int(base_cost * 1.2) if advisor == 'katie' else base_cost

        if not has_sufficient_funds(user, cost):
            return jsonify({'error': f'Need ${cost:,} to hire this employee'}), 400

        deduct_funds(user, cost)
        biz['employees'].append({
            'type': employee_type,
            'hired_at': datetime.now().isoformat(),
        })

        save_users(users)
        save_businesses(businesses)
        add_notification(user, f"✅ Hired {employee_type.replace('_',' ').title()} for ${cost:,}", 'success')

        return jsonify({
            'success': True,
            'message': f"Hired {employee_type.replace('_',' ').title()}",
            'pockets': user.get('pockets', 0),
        })

    # Legacy user-level business_mode system (kept for compatibility)
    role = data.get('role')
    skill = data.get('skill')
    
    if role not in AI_EMPLOYEE_ROLES:
        return jsonify({'error': 'Invalid role'}), 400
    
    if skill not in AI_EMPLOYEE_SKILLS:
        return jsonify({'error': 'Invalid skill level'}), 400
    
    users = load_users()
    user_id = session.get('player_id')
    user = users[user_id]

    ensure_runtime_fields(user)

    # Allow scoping hires to a specific business
    business_id = data.get('business_id') if data else None
    business_mode = init_business_mode(user, business_id)
    
    # Check if already hired
    for employee in business_mode['employees']:
        if employee['role'] == role and employee['skill'] == skill:
            return jsonify({'error': f'{skill.capitalize()} {role} already hired'}), 400
    
    # Check cost
    cost = AI_EMPLOYEE_SKILLS[skill]['cost']
    
    if not has_sufficient_funds(user, cost):
        return jsonify({'error': f'Need ${cost:,} to hire this employee'}), 400
    
    # Deduct cost
    deduct_funds(user, cost)
    
    # Add employee
    business_mode['employees'].append({
        'role': role,
        'skill': skill,
        'hired_at': datetime.now().isoformat(),
        'multiplier': AI_EMPLOYEE_SKILLS[skill]['multiplier']
    })
    
    save_users(users)
    
    add_notification(user, f'✅ Hired {skill.capitalize()} {role} for ${cost:,}', 'success')
    
    return jsonify({
        'success': True,
        'message': f'Hired {skill.capitalize()} {role}',
        'pockets': user['pockets'],
        'bank': user.get('bank', 0)
    })

@bp.route('/api/business_mode/upgrade', methods=['POST'])
def purchase_business_upgrade():
    """Purchase a business upgrade"""
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json(silent=True) or {}

    # Business-level upgrades when business_id is provided
    business_id = data.get('business_id')
    if business_id:
        category = str(data.get('category') or '').strip().lower()
        tier = _coerce_int_amount(data.get('tier'))
        if category not in UPGRADE_TIERS:
            return jsonify({'error': 'Invalid upgrade category'}), 400

        users = load_users()
        user_id = session.get('player_id')
        user = users[user_id]
        ensure_runtime_fields(user)

        businesses = load_businesses()
        biz = businesses.get(str(business_id)) if isinstance(businesses, dict) else None
        if not isinstance(biz, dict):
            return jsonify({'error': 'Business not found'}), 404
        init_business_structure(biz)
        if biz.get('owner') != user_id:
            return jsonify({'error': 'Not your business'}), 403

        current_tier = _coerce_int_amount((biz.get('upgrades', {}) or {}).get(category, 0))
        if tier != current_tier + 1:
            return jsonify({'error': 'Must purchase tiers in order'}), 400

        tiers = UPGRADE_TIERS.get(category, [])
        if tier <= 0 or tier - 1 >= len(tiers):
            return jsonify({'error': 'Invalid tier'}), 400
        tier_info = tiers[tier - 1]
        base_cost = _coerce_int_amount(tier_info.get('cost', 0))
        advisor = get_advisor(user)
        cost = int(base_cost * 1.2) if advisor == 'katie' else base_cost

        if not has_sufficient_funds(user, cost):
            return jsonify({'error': f'Need ${cost:,} for this upgrade'}), 400

        deduct_funds(user, cost)
        biz['upgrades'][category] = tier

        save_users(users)
        save_businesses(businesses)
        add_notification(user, f"✅ Purchased {tier_info.get('name', 'Upgrade')} for ${cost:,}", 'success')

        return jsonify({
            'success': True,
            'message': f"Purchased {tier_info.get('name', 'Upgrade')}",
            'pockets': user.get('pockets', 0),
        })

    # Legacy user-level business_mode upgrades
    category = data.get('category')
    tier = data.get('tier')

    if category not in BUSINESS_UPGRADES:
        return jsonify({'error': 'Invalid upgrade category'}), 400
    
    users = load_users()
    user_id = session.get('player_id')
    user = users[user_id]

    ensure_runtime_fields(user)

    # Allow scoping upgrades to a specific business
    business_id = data.get('business_id') if data else None
    business_mode = init_business_mode(user, business_id)
    
    # Check current tier
    current_tier = business_mode.get('upgrades', {}).get(category, 0)
    
    if tier != current_tier + 1:
        return jsonify({'error': 'Must purchase tiers in order'}), 400
    
    # Get tier info
    tier_index = tier - 1
    if tier_index >= len(BUSINESS_UPGRADES[category]['tiers']):
        return jsonify({'error': 'Invalid tier'}), 400
    
    tier_info = BUSINESS_UPGRADES[category]['tiers'][tier_index]
    cost = tier_info['cost']
    
    if not has_sufficient_funds(user, cost):
        return jsonify({'error': f'Need ${cost:,} for this upgrade'}), 400
    
    # Deduct cost
    deduct_funds(user, cost)
    
    # Apply upgrade
    if 'upgrades' not in business_mode:
        business_mode['upgrades'] = {}
    business_mode['upgrades'][category] = tier
    
    save_users(users)
    
    add_notification(user, f'✅ Purchased {tier_info["name"]} for ${cost:,}', 'success')
    
    return jsonify({
        'success': True,
        'message': f'Purchased {tier_info["name"]}',
        'pockets': user['pockets'],
        'bank': user.get('bank', 0)
    })

@bp.route('/api/business_mode/collect', methods=['POST'])
def collect_business_revenue():
    """Collect accumulated business revenue"""
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not logged in'}), 401
    
    users = load_users()
    user_id = session.get('player_id')
    user = users[user_id]

    ensure_runtime_fields(user)

    # Allow scoping revenue collection to a specific business
    data = request.get_json(silent=True) or {}
    business_id = data.get('business_id')

    # Business-level collection if business_id provided
    if business_id:
        businesses = load_businesses()
        biz = businesses.get(str(business_id)) if isinstance(businesses, dict) else None
        if not isinstance(biz, dict):
            return jsonify({'error': 'Business not found'}), 404
        init_business_structure(biz)
        if biz.get('owner') != user_id:
            return jsonify({'error': 'Not your business'}), 403

        snap = _business_ops_snapshot(biz, owner_user=user)
        net = _coerce_int_amount(snap.get('accumulated_profit', 0))
        if net <= 0:
            return jsonify({'error': 'No revenue to collect'}), 400

        gross = _coerce_int_amount(snap.get('accumulated_gross', 0))
        salary = _coerce_int_amount(snap.get('accumulated_salary', 0))
        tax = _coerce_int_amount(snap.get('accumulated_tax', 0))

        # NEW: Distribute profits to partners if any
        partners = biz.get('partners', [])
        if partners:
            # Calculate total partner ownership
            total_partner_pct = sum(p.get('ownership_pct', 0) for p in partners)
            owner_pct = 100.0 - total_partner_pct
            
            # Owner gets their percentage
            owner_share = int(net * (owner_pct / 100.0))
            user['pockets'] = _coerce_int_amount(user.get('pockets', 0)) + owner_share
            
            # Distribute to partners
            partner_shares = []
            for partner in partners:
                partner_id = partner.get('user_id')
                partner_pct = partner.get('ownership_pct', 0)
                partner_share = int(net * (partner_pct / 100.0))
                
                if partner_id in users:
                    partner_user = users[partner_id]
                    ensure_runtime_fields(partner_user)
                    partner_user['pockets'] = _coerce_int_amount(partner_user.get('pockets', 0)) + partner_share
                    
                    add_notification(
                        partner_user,
                        f'💰 Partnership profit from {biz.get("name", "Business")}: ${partner_share:,} ({partner_pct}%)',
                        'success'
                    )
                    partner_shares.append({
                        'username': partner.get('username', 'Unknown'),
                        'amount': partner_share,
                        'percentage': partner_pct
                    })
        else:
            # No partners, owner gets everything
            user['pockets'] = _coerce_int_amount(user.get('pockets', 0)) + net
            partner_shares = []
            owner_pct = 100.0
            owner_share = net
        
        biz['totalEarnings'] = _coerce_int_amount(biz.get('totalEarnings', 0)) + net
        biz['totalGrossRevenue'] = _coerce_int_amount(biz.get('totalGrossRevenue', 0)) + gross
        biz['totalSalariesPaid'] = _coerce_int_amount(biz.get('totalSalariesPaid', 0)) + salary
        biz['totalTaxesPaid'] = _coerce_int_amount(biz.get('totalTaxesPaid', 0)) + tax
        biz['lastRevenueAt'] = datetime.now().isoformat()

        config = load_config()
        _apply_business_tax_to_config(config, tax)
        save_config(config)

        save_users(users)
        save_businesses(businesses)

        msg = f'💰 Collected ${owner_share:,} ({owner_pct:.1f}%) from {biz.get("name", "business")}'
        if partner_shares:
            msg += f' (Distributed ${net - owner_share:,} to {len(partner_shares)} partner(s))'
        
        add_notification(user, msg, 'success')

        try:
            update_achievement_stat(user_id, 'business_revenue', owner_share)
            check_all_achievements(user_id)
        except Exception as e:
            print(f"Warning: achievement update failed during business collection: {e}")

        return jsonify({
            'success': True,
            'message': f'Collected ${owner_share:,} (Your {owner_pct:.1f}%)',
            'revenue': owner_share,
            'total_net': net,
            'gross': gross,
            'salary': salary,
            'tax': tax,
            'partner_shares': partner_shares,
            'tax_rate_percent': round(float(snap.get('tax_rate', 0.0)) * 100.0, 2),
            'pockets': user.get('pockets', 0),
            'total_revenue': _coerce_int_amount(biz.get('totalEarnings', 0)),
        })

    business_mode = init_business_mode(user, business_id)

    # Calculate revenue (legacy)
    revenue = calculate_business_revenue(business_mode)
    
    if revenue <= 0:
        return jsonify({'error': 'No revenue to collect'}), 400
    
    # Add to balance
    user['pockets'] += revenue
    business_mode['total_revenue'] += revenue
    business_mode['last_collection'] = datetime.now().isoformat()
    
    save_users(users)
    
    add_notification(user, f'💰 Collected ${revenue:,} from business operations', 'success')
    
    # Update achievement (best-effort — don't let achievement failures break collection)
    try:
        update_achievement_stat(user_id, 'business_revenue', revenue)
        check_all_achievements(user_id)
    except Exception as e:
        print(f"Warning: achievement update failed during collection: {e}")

    return jsonify({
        'success': True,
        'message': f'Collected ${revenue:,}',
        'revenue': revenue,
        'pockets': user['pockets'],
        'total_revenue': business_mode['total_revenue']
    })


@bp.route('/api/businesses/management_summary')
def businesses_management_summary():
    """Return an aggregated Business Management summary across the user's businesses.

    If the user has no businesses yet, fall back to legacy user['business_mode'] summary.
    """
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not logged in'}), 401

    users = load_users()
    user_id = session.get('player_id')
    user = users[user_id]

    ensure_runtime_fields(user)

    businesses = load_businesses()

    biz_ids = user.get('businesses', []) if isinstance(user.get('businesses', []), list) else []

    total_employees = 0
    total_upgrades = 0
    total_revenue_sum = 0
    total_accumulated = 0
    total_revenue_rate = 0
    per_business = []

    if biz_ids:
        for bid in biz_ids:
            biz = businesses.get(bid) if isinstance(businesses, dict) else None
            if not isinstance(biz, dict):
                continue
            init_business_structure(biz)
            snap = _business_ops_snapshot(biz, owner_user=user)

            upgrades = biz.get('upgrades', {}) if isinstance(biz.get('upgrades', {}), dict) else {}
            up_count = sum(1 for t in upgrades.values() if _coerce_int_amount(t) > 0)

            acc = _coerce_int_amount(snap.get('accumulated_profit', 0))
            rate = _coerce_int_amount(snap.get('net_per_hour', 0))
            total_employees += _coerce_int_amount(snap.get('employee_count', 0))
            total_upgrades += up_count
            total_revenue_sum += _coerce_int_amount(biz.get('totalEarnings', 0))
            total_accumulated += acc
            total_revenue_rate += rate

            per_business.append({
                'id': str(bid),
                'name': biz.get('name', str(bid)),
                'employees': _coerce_int_amount(snap.get('employee_count', 0)),
                'upgrades': up_count,
                'total_revenue': _coerce_int_amount(biz.get('totalEarnings', 0)),
                'accumulated_revenue': acc,
                'revenue_rate': rate
            })
    else:
        # Legacy fallback summary
        all_businesses = businesses
        bm_map = user.get('business_mode', {}) or {}
        for key, bm in bm_map.items():
            if not isinstance(bm, dict):
                continue
            employees = bm.get('employees', [])
            upgrades = bm.get('upgrades', {})

            total_employees += len(employees)
            total_upgrades += sum(1 for t in upgrades.values() if t and t > 0)
            total_revenue_sum += int(bm.get('total_revenue', 0))

            try:
                acc = calculate_business_revenue(bm)
            except Exception:
                acc = 0
            total_accumulated += int(acc)

            base_revenue = 1000
            employee_count = len(employees)
            employee_multiplier = 0
            for emp in employees:
                skill = emp.get('skill', 'novice')
                employee_multiplier += AI_EMPLOYEE_SKILLS.get(skill, {}).get('multiplier', 0)

            employee_factor = 1 + (0.5 * employee_count) + employee_multiplier

            upgrade_multiplier = 1.0
            for category, tier in (upgrades or {}).items():
                if category in BUSINESS_UPGRADES and tier > 0:
                    tier_index = tier - 1
                    if tier_index < len(BUSINESS_UPGRADES[category]['tiers']):
                        upgrade_multiplier += BUSINESS_UPGRADES[category]['tiers'][tier_index]['effect']

            revenue_rate = int(base_revenue * employee_factor * upgrade_multiplier)
            total_revenue_rate += revenue_rate

            display_name = key
            if key != '__default__':
                biz = all_businesses.get(key) if isinstance(all_businesses, dict) else None
                if isinstance(biz, dict) and 'name' in biz:
                    display_name = biz['name']

            per_business.append({
                'id': key,
                'name': display_name,
                'employees': len(employees),
                'upgrades': sum(1 for t in (upgrades or {}).values() if t and t > 0),
                'total_revenue': int(bm.get('total_revenue', 0)),
                'accumulated_revenue': int(acc),
                'revenue_rate': revenue_rate
            })

    return jsonify({
        'total_employees': total_employees,
        'total_upgrades': total_upgrades,
        'total_revenue_sum': total_revenue_sum,
        'total_accumulated_revenue': total_accumulated,
        'total_revenue_rate': total_revenue_rate,
        'per_business': per_business
    })

