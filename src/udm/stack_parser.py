"""Smart Stack Parser — offline keyword mapping for tech stack detection.

Parses natural-language prompts (English & Hinglish) into a list of tool
keys that match entries in tools.json.  No external API or LLM required.

Three layers of matching (checked in order):
    1. **Stack presets** — "MERN", "Django", "LAMP", etc.
    2. **Problem / domain** — "e-commerce", "chat app", "blog", etc.
    3. **Individual tech aliases** — "python", "mongo", "docker", etc.

Supported input examples:
    "MERN stack project banao"
    "e-commerce website banana hai"
    "chat application banao real-time wali"
    "machine learning model train karna hai"
    "mobile app banani hai Android ke liye"
    "REST API banana hai with authentication"
    "portfolio website banao"
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# ── Hinglish / noise words to strip before matching ─────────────────────
_NOISE_WORDS: set[str] = {
    # Hinglish verbs & helpers
    "banao", "banana", "hai", "karo", "karna", "chahiye", "chaiye",
    "lagao", "lagana", "install", "setup", "kro", "krdo", "krna",
    "de", "do", "dijiye", "dena", "use", "using", "wala", "wali",
    "wale", "vale", "vala", "vali",
    "hoga", "hogi", "hoge", "hain", "tha", "thi", "the",
    "raha", "rahi", "rahe", "rha", "rhi",
    "sakta", "sakti", "sakte", "paye", "paaye",
    "dunga", "dungi", "denge",
    "karunga", "karungi", "karenge",
    "bata", "batao", "batana", "bataiye", "samjhao", "samjha",
    "dikhao", "dikhana", "dikha",
    "suggest", "recommend", "list", "show",
    # Hinglish connectors / fillers
    "ka", "ke", "ki", "ko", "me", "mein", "se", "pe", "par",
    "liye", "aur", "or", "bhi", "sab", "ek", "naya",
    "naye", "nayi", "mujhe", "mereko", "mere", "mera", "apna",
    "sabhi", "saare", "pura", "poora", "puri", "yeh", "ye", "wo",
    "woh", "iska", "uska", "unka", "hamara", "humara",
    "jaise", "jaisa", "jaisi", "tarah", "type",
    "accha", "acha", "best", "top", "good",
    "koi", "kuch", "thoda", "bahut", "bohot", "zyada",
    "abhi", "jaldi", "turant",
    # English fillers
    "a", "an", "the", "for", "with", "on", "in", "to", "and",
    "my", "i", "want", "need", "make", "create", "build", "start",
    "new", "project", "app", "application", "website", "web",
    "please", "pls", "plz", "set", "up", "develop", "development",
    "based", "stack", "tech", "full", "fullstack", "full-stack",
    "like", "similar", "something", "thing", "stuff",
    "would", "could", "should", "can", "will",
    "it", "its", "that", "this", "those", "these",
    "what", "which", "how", "where", "give", "me",
    "tools", "tool", "software", "technologies", "technology",
    "required", "requirements", "needed", "needs",
    "simple", "basic", "advanced", "complex", "complete",
    "professional", "production", "ready",
    "help", "about", "from", "into",
}


# ══════════════════════════════════════════════════════════════════════════
#  LAYER 1 — Named Tech Stack Presets
# ══════════════════════════════════════════════════════════════════════════

STACK_PRESETS: dict[str, list[str]] = {

    # ── JavaScript / Node Full-Stack ────────────────────────────────
    "mern":        ["mongodb", "nodejs", "npm", "git", "vscode"],
    "mean":        ["mongodb", "nodejs", "npm", "typescript", "git", "vscode"],
    "mevn":        ["mongodb", "nodejs", "npm", "git", "vscode"],
    "nextjs":      ["nodejs", "npm", "typescript", "git", "vscode"],
    "next":        ["nodejs", "npm", "typescript", "git", "vscode"],
    "nuxtjs":      ["nodejs", "npm", "git", "vscode"],
    "nuxt":        ["nodejs", "npm", "git", "vscode"],
    "svelte":      ["nodejs", "npm", "git", "vscode"],
    "sveltekit":   ["nodejs", "npm", "git", "vscode"],
    "remix":       ["nodejs", "npm", "typescript", "git", "vscode"],
    "gatsby":      ["nodejs", "npm", "git", "vscode"],
    "astro":       ["nodejs", "npm", "git", "vscode"],
    "expressjs":   ["nodejs", "npm", "git"],
    "express":     ["nodejs", "npm", "git"],
    "nestjs":      ["nodejs", "npm", "typescript", "git", "vscode"],
    "hono":        ["nodejs", "npm", "typescript", "git", "vscode"],
    "fastify":     ["nodejs", "npm", "git", "vscode"],

    # ── Python Full-Stack / Frameworks ──────────────────────────────
    "django":      ["python", "pip", "postgres", "git", "vscode"],
    "flask":       ["python", "pip", "git", "vscode"],
    "fastapi":     ["python", "pip", "git", "vscode", "docker"],
    "streamlit":   ["python", "pip", "git", "vscode"],
    "gradio":      ["python", "pip", "git", "vscode"],

    # ── PHP Stacks ──────────────────────────────────────────────────
    "lamp":        ["php", "mysql", "git", "vscode"],
    "lemp":        ["php", "mysql", "git", "vscode"],
    "laravel":     ["php", "composer", "nodejs", "npm", "mysql", "git", "vscode"],
    "symfony":     ["php", "composer", "git", "vscode"],
    "wordpress":   ["php", "composer", "mysql", "git"],
    "drupal":      ["php", "composer", "mysql", "git"],
    "magento":     ["php", "composer", "mysql", "redis", "git", "vscode"],
    "codeigniter": ["php", "composer", "mysql", "git", "vscode"],
    "cakephp":     ["php", "composer", "mysql", "git", "vscode"],

    # ── Ruby Stacks ─────────────────────────────────────────────────
    "rails":         ["ruby", "gem", "nodejs", "npm", "postgres", "redis", "git", "vscode"],
    "rubyonrails":   ["ruby", "gem", "nodejs", "npm", "postgres", "redis", "git", "vscode"],
    "sinatra":       ["ruby", "gem", "git", "vscode"],

    # ── Mobile Stacks ───────────────────────────────────────────────
    "flutter":       ["flutter", "dart", "android_sdk", "git", "vscode"],
    "reactnative":   ["nodejs", "npm", "react_native", "android_sdk", "git", "vscode"],
    "react-native":  ["nodejs", "npm", "react_native", "android_sdk", "git", "vscode"],
    "android":       ["java", "android_sdk", "gradle", "git", "vscode"],
    "kotlin-android": ["kotlin", "android_sdk", "gradle", "git", "vscode"],
    "ios":           ["swift", "git"],
    "ionic":         ["nodejs", "npm", "typescript", "android_sdk", "git", "vscode"],
    "capacitor":     ["nodejs", "npm", "typescript", "android_sdk", "git", "vscode"],
    "expo":          ["nodejs", "npm", "git", "vscode"],

    # ── Java Stacks ─────────────────────────────────────────────────
    "spring":        ["java", "maven", "postgres", "git", "vscode"],
    "springboot":    ["java", "maven", "postgres", "docker", "git", "vscode"],
    "spring-boot":   ["java", "maven", "postgres", "docker", "git", "vscode"],
    "quarkus":       ["java", "maven", "docker", "git", "vscode"],
    "micronaut":     ["java", "maven", "git", "vscode"],
    "dropwizard":    ["java", "maven", "git", "vscode"],
    "struts":        ["java", "maven", "git", "vscode"],
    "hibernate":     ["java", "maven", "mysql", "git", "vscode"],

    # ── .NET Stacks ─────────────────────────────────────────────────
    "dotnet":    ["csharp", "dotnet", "git", "vscode"],
    "aspnet":    ["csharp", "dotnet", "postgres", "git", "vscode"],
    "asp.net":   ["csharp", "dotnet", "postgres", "git", "vscode"],
    "blazor":    ["csharp", "dotnet", "git", "vscode"],
    "maui":      ["csharp", "dotnet", "git", "vscode"],
    "wpf":       ["csharp", "dotnet", "git", "vscode"],
    "winforms":  ["csharp", "dotnet", "git", "vscode"],
    "unity":     ["csharp", "dotnet", "git", "vscode"],
    "xamarin":   ["csharp", "dotnet", "android_sdk", "git", "vscode"],

    # ── Go Stacks ───────────────────────────────────────────────────
    "gin":       ["go", "docker", "postgres", "git", "vscode"],
    "fiber":     ["go", "docker", "git", "vscode"],
    "gofiber":   ["go", "docker", "git", "vscode"],
    "echo":      ["go", "docker", "git", "vscode"],
    "beego":     ["go", "git", "vscode"],

    # ── Rust Stacks ─────────────────────────────────────────────────
    "actix":     ["rust", "cargo", "docker", "git", "vscode"],
    "rocket":    ["rust", "cargo", "git", "vscode"],
    "axum":      ["rust", "cargo", "docker", "git", "vscode"],
    "tauri":     ["rust", "cargo", "nodejs", "npm", "git", "vscode"],
    "yew":       ["rust", "cargo", "git", "vscode"],

    # ── Elixir / Erlang ─────────────────────────────────────────────
    "phoenix":   ["elixir", "erlang", "nodejs", "npm", "postgres", "git", "vscode"],
    "livebook":  ["elixir", "erlang", "git", "vscode"],

    # ── Data Science / AI / ML ──────────────────────────────────────
    "datascience":       ["python", "pip", "jupyter", "anaconda", "git", "vscode"],
    "data-science":      ["python", "pip", "jupyter", "anaconda", "git", "vscode"],
    "machinelearning":   ["python", "pip", "jupyter", "tensorflow", "pytorch", "git", "vscode"],
    "machine-learning":  ["python", "pip", "jupyter", "tensorflow", "pytorch", "git", "vscode"],
    "ml":                ["python", "pip", "jupyter", "tensorflow", "pytorch", "git", "vscode"],
    "ai":                ["python", "pip", "jupyter", "tensorflow", "pytorch", "cuda", "git", "vscode"],
    "deeplearning":      ["python", "pip", "jupyter", "tensorflow", "pytorch", "cuda", "git", "vscode"],
    "deep-learning":     ["python", "pip", "jupyter", "tensorflow", "pytorch", "cuda", "git", "vscode"],
    "nlp":               ["python", "pip", "jupyter", "pytorch", "git", "vscode"],
    "computervision":    ["python", "pip", "jupyter", "pytorch", "cuda", "git", "vscode"],
    "computer-vision":   ["python", "pip", "jupyter", "pytorch", "cuda", "git", "vscode"],
    "llm":               ["python", "pip", "jupyter", "pytorch", "cuda", "git", "vscode"],
    "genai":             ["python", "pip", "jupyter", "pytorch", "cuda", "git", "vscode"],

    # ── DevOps / Infra ──────────────────────────────────────────────
    "devops":           ["docker", "kubernetes", "terraform", "ansible", "git", "vscode"],
    "cicd":             ["docker", "git", "gh_cli"],
    "ci/cd":            ["docker", "git", "gh_cli"],
    "containerization": ["docker", "podman", "kubernetes", "helm"],
    "microservices":    ["docker", "kubernetes", "nodejs", "npm", "git", "postman"],
    "serverless":       ["nodejs", "npm", "aws_cli", "docker", "git", "vscode"],
    "cloud-native":     ["docker", "kubernetes", "helm", "terraform", "git", "vscode"],
    "cloudnative":      ["docker", "kubernetes", "helm", "terraform", "git", "vscode"],
    "infrastructure":   ["terraform", "ansible", "docker", "git", "vscode"],

    # ── Blockchain / Web3 ───────────────────────────────────────────
    "blockchain":  ["nodejs", "npm", "solidity", "git", "vscode"],
    "ethereum":    ["nodejs", "npm", "solidity", "git", "vscode"],
    "web3":        ["nodejs", "npm", "solidity", "git", "vscode"],
    "solidity":    ["nodejs", "npm", "solidity", "git", "vscode"],
    "hardhat":     ["nodejs", "npm", "solidity", "git", "vscode"],
    "truffle":     ["nodejs", "npm", "solidity", "git", "vscode"],
    "dapp":        ["nodejs", "npm", "solidity", "git", "vscode"],

    # ── Game Dev ────────────────────────────────────────────────────
    "pygame":      ["python", "pip", "git", "vscode"],
    "godot":       ["git", "vscode"],
    "unreal":      ["gpp", "cmake", "git", "vscode"],
    "monogame":    ["csharp", "dotnet", "git", "vscode"],

    # ── Misc Combos ─────────────────────────────────────────────────
    "jamstack":    ["nodejs", "npm", "git", "vscode"],
    "t3":          ["nodejs", "npm", "typescript", "postgres", "git", "vscode"],
    "t3stack":     ["nodejs", "npm", "typescript", "postgres", "git", "vscode"],
    "supabase":    ["nodejs", "npm", "typescript", "postgres", "docker", "git", "vscode"],
    "firebase":    ["nodejs", "npm", "git", "gcloud", "vscode"],
    "electron":    ["nodejs", "npm", "git", "vscode"],
    "pwa":         ["nodejs", "npm", "git", "vscode"],
    "graphql":     ["nodejs", "npm", "typescript", "git", "vscode", "postman"],
    "grpc":        ["go", "protobuf", "git", "vscode"],
    "rabbitmq":    ["docker", "nodejs", "npm", "git", "vscode"],
    "kafka":       ["java", "maven", "docker", "git", "vscode"],
    "elasticsearch": ["java", "docker", "git", "vscode"],
}


# ══════════════════════════════════════════════════════════════════════════
#  LAYER 2 — Problem / Domain / Use-Case Keywords
# ══════════════════════════════════════════════════════════════════════════
# Maps what the user wants to BUILD (not a stack name) → tool keys.
# Checked when no stack preset matches.

PROBLEM_DOMAINS: dict[str, list[str]] = {

    # ── Web: E-commerce / Shopping ──────────────────────────────────
    "ecommerce":    ["nodejs", "npm", "mongodb", "redis", "docker", "git", "vscode"],
    "e-commerce":   ["nodejs", "npm", "mongodb", "redis", "docker", "git", "vscode"],
    "shopping":     ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],
    "store":        ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],
    "shop":         ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],
    "marketplace":  ["nodejs", "npm", "mongodb", "redis", "docker", "git", "vscode"],
    "payment":      ["nodejs", "npm", "mongodb", "git", "vscode"],
    "cart":         ["nodejs", "npm", "mongodb", "git", "vscode"],
    # Hinglish
    "dukaan":       ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],

    # ── Web: Social / Chat / Real-time ──────────────────────────────
    "chat":         ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],
    "messaging":    ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],
    "realtime":     ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],
    "real-time":    ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],
    "websocket":    ["nodejs", "npm", "redis", "git", "vscode"],
    "socket":       ["nodejs", "npm", "redis", "git", "vscode"],
    "socialmedia":  ["nodejs", "npm", "mongodb", "redis", "docker", "git", "vscode"],
    "social-media": ["nodejs", "npm", "mongodb", "redis", "docker", "git", "vscode"],
    "social":       ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],
    "forum":        ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],
    "community":    ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],
    "notification": ["nodejs", "npm", "redis", "git", "vscode"],
    "notifications": ["nodejs", "npm", "redis", "git", "vscode"],

    # ── Web: Blog / CMS / Content ───────────────────────────────────
    "blog":         ["nodejs", "npm", "mongodb", "git", "vscode"],
    "cms":          ["php", "composer", "mysql", "git", "vscode"],
    "content":      ["nodejs", "npm", "mongodb", "git", "vscode"],
    "news":         ["nodejs", "npm", "mongodb", "git", "vscode"],
    "magazine":     ["nodejs", "npm", "mongodb", "git", "vscode"],
    "wiki":         ["nodejs", "npm", "mongodb", "git", "vscode"],

    # ── Web: Portfolio / Personal ───────────────────────────────────
    "portfolio":    ["nodejs", "npm", "git", "vscode"],
    "resume":       ["nodejs", "npm", "git", "vscode"],
    "landing":      ["nodejs", "npm", "git", "vscode"],
    "landingpage":  ["nodejs", "npm", "git", "vscode"],
    "personal":     ["nodejs", "npm", "git", "vscode"],
    "static":       ["nodejs", "npm", "git", "vscode"],

    # ── Web: Dashboard / Admin ──────────────────────────────────────
    "dashboard":    ["nodejs", "npm", "typescript", "postgres", "git", "vscode"],
    "admin":        ["nodejs", "npm", "typescript", "postgres", "git", "vscode"],
    "adminpanel":   ["nodejs", "npm", "typescript", "postgres", "git", "vscode"],
    "analytics":    ["python", "pip", "jupyter", "postgres", "git", "vscode"],
    "reporting":    ["python", "pip", "jupyter", "postgres", "git", "vscode"],
    "monitoring":   ["docker", "nodejs", "npm", "postgres", "git", "vscode"],
    "crm":          ["nodejs", "npm", "typescript", "postgres", "redis", "git", "vscode"],
    "erp":          ["java", "maven", "postgres", "redis", "docker", "git", "vscode"],

    # ── Backend / API ───────────────────────────────────────────────
    "api":          ["nodejs", "npm", "mongodb", "postman", "git", "vscode"],
    "rest":         ["nodejs", "npm", "mongodb", "postman", "git", "vscode"],
    "restapi":      ["nodejs", "npm", "mongodb", "postman", "git", "vscode"],
    "rest-api":     ["nodejs", "npm", "mongodb", "postman", "git", "vscode"],
    "backend":      ["nodejs", "npm", "mongodb", "postman", "docker", "git", "vscode"],
    "server":       ["nodejs", "npm", "mongodb", "docker", "git", "vscode"],
    "microservice": ["docker", "kubernetes", "nodejs", "npm", "git", "postman", "vscode"],
    "authentication": ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],
    "auth":         ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],
    "login":        ["nodejs", "npm", "mongodb", "git", "vscode"],
    "oauth":        ["nodejs", "npm", "mongodb", "git", "vscode"],
    "jwt":          ["nodejs", "npm", "mongodb", "git", "vscode"],

    # ── Frontend ────────────────────────────────────────────────────
    "frontend":     ["nodejs", "npm", "typescript", "git", "vscode"],
    "ui":           ["nodejs", "npm", "git", "vscode"],
    "spa":          ["nodejs", "npm", "typescript", "git", "vscode"],
    "responsive":   ["nodejs", "npm", "git", "vscode"],

    # ── Mobile ──────────────────────────────────────────────────────
    "mobile":       ["flutter", "dart", "android_sdk", "git", "vscode"],
    "mobileapp":    ["flutter", "dart", "android_sdk", "git", "vscode"],
    "mobile-app":   ["flutter", "dart", "android_sdk", "git", "vscode"],
    "crossplatform": ["flutter", "dart", "android_sdk", "git", "vscode"],
    "cross-platform": ["flutter", "dart", "android_sdk", "git", "vscode"],
    "hybrid":       ["flutter", "dart", "android_sdk", "git", "vscode"],

    # ── Desktop ─────────────────────────────────────────────────────
    "desktop":      ["python", "pip", "git", "vscode"],
    "desktopapp":   ["python", "pip", "git", "vscode"],
    "desktop-app":  ["python", "pip", "git", "vscode"],
    "gui":          ["python", "pip", "git", "vscode"],

    # ── CLI / Scripting / Automation ─────────────────────────────────
    "cli":          ["python", "pip", "git", "vscode"],
    "commandline":  ["python", "pip", "git", "vscode"],
    "command-line": ["python", "pip", "git", "vscode"],
    "terminal":     ["python", "pip", "git", "vscode"],
    "script":       ["python", "pip", "git", "vscode"],
    "scripting":    ["python", "pip", "git", "vscode"],
    "automation":   ["python", "pip", "docker", "git", "vscode"],
    "bot":          ["python", "pip", "git", "vscode"],
    "chatbot":      ["python", "pip", "mongodb", "git", "vscode"],
    "discord":      ["nodejs", "npm", "git", "vscode"],
    "telegram":     ["python", "pip", "git", "vscode"],
    "whatsapp":     ["nodejs", "npm", "git", "vscode"],
    "scraping":     ["python", "pip", "git", "vscode"],
    "webscraping":  ["python", "pip", "git", "vscode"],
    "web-scraping": ["python", "pip", "git", "vscode"],
    "crawler":      ["python", "pip", "git", "vscode"],

    # ── AI / ML / Data ──────────────────────────────────────────────
    "prediction":   ["python", "pip", "jupyter", "tensorflow", "git", "vscode"],
    "classification": ["python", "pip", "jupyter", "pytorch", "git", "vscode"],
    "regression":   ["python", "pip", "jupyter", "git", "vscode"],
    "recommendation": ["python", "pip", "jupyter", "pytorch", "git", "vscode"],
    "imageprocessing": ["python", "pip", "jupyter", "pytorch", "cuda", "git", "vscode"],
    "image-processing": ["python", "pip", "jupyter", "pytorch", "cuda", "git", "vscode"],
    "objectdetection": ["python", "pip", "jupyter", "pytorch", "cuda", "git", "vscode"],
    "object-detection": ["python", "pip", "jupyter", "pytorch", "cuda", "git", "vscode"],
    "facerecognition": ["python", "pip", "jupyter", "pytorch", "cuda", "git", "vscode"],
    "face-recognition": ["python", "pip", "jupyter", "pytorch", "cuda", "git", "vscode"],
    "speechrecognition": ["python", "pip", "jupyter", "pytorch", "git", "vscode"],
    "speech":       ["python", "pip", "jupyter", "pytorch", "git", "vscode"],
    "textgeneration": ["python", "pip", "jupyter", "pytorch", "cuda", "git", "vscode"],
    "sentiment":    ["python", "pip", "jupyter", "pytorch", "git", "vscode"],
    "training":     ["python", "pip", "jupyter", "pytorch", "cuda", "git", "vscode"],
    "model":        ["python", "pip", "jupyter", "pytorch", "git", "vscode"],
    "dataset":      ["python", "pip", "jupyter", "git", "vscode"],
    "dataanalysis": ["python", "pip", "jupyter", "anaconda", "git", "vscode"],
    "data-analysis": ["python", "pip", "jupyter", "anaconda", "git", "vscode"],
    "visualization": ["python", "pip", "jupyter", "git", "vscode"],
    "etl":          ["python", "pip", "postgres", "docker", "git", "vscode"],
    "pipeline":     ["python", "pip", "docker", "git", "vscode"],
    "datapipeline": ["python", "pip", "docker", "git", "vscode"],
    "bigdata":      ["python", "pip", "jupyter", "docker", "git", "vscode"],
    "big-data":     ["python", "pip", "jupyter", "docker", "git", "vscode"],

    # ── Game Dev ────────────────────────────────────────────────────
    "game":         ["python", "pip", "git", "vscode"],
    "gaming":       ["python", "pip", "git", "vscode"],
    "gamedev":      ["csharp", "dotnet", "git", "vscode"],
    "game-dev":     ["csharp", "dotnet", "git", "vscode"],
    "2dgame":       ["python", "pip", "git", "vscode"],
    "3dgame":       ["csharp", "dotnet", "git", "vscode"],

    # ── IoT / Embedded / Hardware ───────────────────────────────────
    "iot":          ["python", "pip", "mqtt", "docker", "git", "vscode"],
    "embedded":     ["gcc", "cmake", "git", "vscode"],
    "arduino":      ["gcc", "git", "vscode"],
    "raspberrypi":  ["python", "pip", "git", "vscode"],
    "raspberry":    ["python", "pip", "git", "vscode"],
    "sensor":       ["python", "pip", "git", "vscode"],
    "hardware":     ["gcc", "cmake", "git", "vscode"],

    # ── Security / Hacking ──────────────────────────────────────────
    "security":     ["python", "pip", "docker", "git", "vscode"],
    "cybersecurity": ["python", "pip", "docker", "git", "vscode"],
    "hacking":      ["python", "pip", "git", "vscode"],
    "pentest":      ["python", "pip", "docker", "git", "vscode"],
    "pentesting":   ["python", "pip", "docker", "git", "vscode"],
    "ctf":          ["python", "pip", "git", "vscode"],

    # ── Cloud / Deployment ──────────────────────────────────────────
    "deploy":       ["docker", "git", "vscode"],
    "deployment":   ["docker", "kubernetes", "git", "vscode"],
    "hosting":      ["docker", "git", "vscode"],
    "aws":          ["aws_cli", "docker", "terraform", "git", "vscode"],
    "azure":        ["azure_cli", "docker", "terraform", "git", "vscode"],
    "gcp":          ["gcloud", "docker", "terraform", "git", "vscode"],
    "cloud":        ["docker", "kubernetes", "terraform", "git", "vscode"],

    # ── Testing / QA ────────────────────────────────────────────────
    "testing":      ["nodejs", "npm", "git", "vscode"],
    "unittest":     ["python", "pip", "git", "vscode"],
    "e2e":          ["nodejs", "npm", "git", "vscode"],
    "selenium":     ["python", "pip", "git", "vscode"],
    "cypress":      ["nodejs", "npm", "git", "vscode"],
    "qa":           ["nodejs", "npm", "docker", "git", "vscode"],

    # ── Compiler / Systems Programming ──────────────────────────────
    "compiler":     ["gcc", "gpp", "cmake", "make", "git", "vscode"],
    "operating":    ["gcc", "gpp", "cmake", "make", "nasm", "git", "vscode"],
    "os":           ["gcc", "gpp", "cmake", "make", "nasm", "git", "vscode"],
    "kernel":       ["gcc", "gpp", "cmake", "make", "git", "vscode"],
    "driver":       ["gcc", "gpp", "cmake", "git", "vscode"],
    "systems":      ["rust", "cargo", "git", "vscode"],
    "lowlevel":     ["gcc", "gpp", "cmake", "nasm", "gdb", "git", "vscode"],
    "low-level":    ["gcc", "gpp", "cmake", "nasm", "gdb", "git", "vscode"],
    "assembly":     ["nasm", "gcc", "gdb", "git", "vscode"],

    # ── Database-centric ────────────────────────────────────────────
    "database":     ["postgres", "mysql", "mongodb", "redis", "docker", "git", "vscode"],
    "sql":          ["postgres", "mysql", "git", "vscode"],
    "nosql":        ["mongodb", "redis", "git", "vscode"],
    "caching":      ["redis", "docker", "git", "vscode"],
    "cache":        ["redis", "docker", "git", "vscode"],

    # ── Media / Streaming ───────────────────────────────────────────
    "video":        ["nodejs", "npm", "ffmpeg", "git", "vscode"],
    "streaming":    ["nodejs", "npm", "ffmpeg", "redis", "docker", "git", "vscode"],
    "audio":        ["python", "pip", "ffmpeg", "git", "vscode"],
    "image":        ["python", "pip", "imagemagick", "git", "vscode"],
    "media":        ["nodejs", "npm", "ffmpeg", "imagemagick", "git", "vscode"],
    "youtube":      ["python", "pip", "ffmpeg", "git", "vscode"],

    # ── Education / LMS ─────────────────────────────────────────────
    "lms":          ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],
    "learning":     ["nodejs", "npm", "mongodb", "git", "vscode"],
    "education":    ["nodejs", "npm", "mongodb", "git", "vscode"],
    "course":       ["nodejs", "npm", "mongodb", "git", "vscode"],
    "quiz":         ["nodejs", "npm", "mongodb", "git", "vscode"],
    "exam":         ["nodejs", "npm", "mongodb", "postgres", "git", "vscode"],

    # ── Finance / Fintech ───────────────────────────────────────────
    "fintech":      ["nodejs", "npm", "typescript", "postgres", "redis", "docker", "git", "vscode"],
    "finance":      ["python", "pip", "jupyter", "postgres", "git", "vscode"],
    "banking":      ["java", "maven", "postgres", "redis", "docker", "git", "vscode"],
    "trading":      ["python", "pip", "jupyter", "redis", "git", "vscode"],
    "crypto":       ["nodejs", "npm", "solidity", "mongodb", "git", "vscode"],
    "cryptocurrency": ["nodejs", "npm", "solidity", "mongodb", "git", "vscode"],
    "wallet":       ["nodejs", "npm", "solidity", "mongodb", "git", "vscode"],

    # ── Health / Medical ────────────────────────────────────────────
    "health":       ["nodejs", "npm", "typescript", "postgres", "docker", "git", "vscode"],
    "medical":      ["python", "pip", "postgres", "docker", "git", "vscode"],
    "hospital":     ["nodejs", "npm", "typescript", "postgres", "docker", "git", "vscode"],
    "telemedicine": ["nodejs", "npm", "typescript", "mongodb", "redis", "docker", "git", "vscode"],

    # ── Food / Delivery ─────────────────────────────────────────────
    "food":         ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],
    "delivery":     ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],
    "restaurant":   ["nodejs", "npm", "mongodb", "git", "vscode"],
    "recipe":       ["nodejs", "npm", "mongodb", "git", "vscode"],
    "swiggy":       ["nodejs", "npm", "mongodb", "redis", "docker", "git", "vscode"],
    "zomato":       ["nodejs", "npm", "mongodb", "redis", "docker", "git", "vscode"],
    "uber":         ["nodejs", "npm", "mongodb", "redis", "docker", "kubernetes", "git", "vscode"],

    # ── Travel / Booking ────────────────────────────────────────────
    "travel":       ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],
    "booking":      ["nodejs", "npm", "postgres", "redis", "git", "vscode"],
    "hotel":        ["nodejs", "npm", "postgres", "redis", "git", "vscode"],
    "flight":       ["nodejs", "npm", "postgres", "redis", "git", "vscode"],
    "ticket":       ["nodejs", "npm", "postgres", "redis", "git", "vscode"],
    "reservation":  ["nodejs", "npm", "postgres", "redis", "git", "vscode"],

    # ── Misc domains ────────────────────────────────────────────────
    "calendar":     ["nodejs", "npm", "mongodb", "git", "vscode"],
    "todo":         ["nodejs", "npm", "mongodb", "git", "vscode"],
    "todolist":     ["nodejs", "npm", "mongodb", "git", "vscode"],
    "task":         ["nodejs", "npm", "mongodb", "git", "vscode"],
    "taskmanager":  ["nodejs", "npm", "mongodb", "git", "vscode"],
    "kanban":       ["nodejs", "npm", "mongodb", "git", "vscode"],
    "trello":       ["nodejs", "npm", "mongodb", "git", "vscode"],
    "email":        ["nodejs", "npm", "postgres", "redis", "git", "vscode"],
    "newsletter":   ["nodejs", "npm", "postgres", "git", "vscode"],
    "survey":       ["nodejs", "npm", "mongodb", "git", "vscode"],
    "poll":         ["nodejs", "npm", "mongodb", "git", "vscode"],
    "voting":       ["nodejs", "npm", "mongodb", "git", "vscode"],
    "inventory":    ["nodejs", "npm", "postgres", "git", "vscode"],
    "warehouse":    ["nodejs", "npm", "postgres", "git", "vscode"],
    "logistics":    ["nodejs", "npm", "postgres", "redis", "docker", "git", "vscode"],
    "tracking":     ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],
    "maps":         ["nodejs", "npm", "git", "vscode"],
    "location":     ["nodejs", "npm", "mongodb", "git", "vscode"],
    "gps":          ["nodejs", "npm", "mongodb", "git", "vscode"],
    "weather":      ["nodejs", "npm", "git", "vscode"],
    "music":        ["nodejs", "npm", "mongodb", "ffmpeg", "git", "vscode"],
    "spotify":      ["nodejs", "npm", "mongodb", "git", "vscode"],
    "netflix":      ["nodejs", "npm", "mongodb", "redis", "ffmpeg", "docker", "git", "vscode"],
    "clone":        ["nodejs", "npm", "mongodb", "git", "vscode"],
    "pdf":          ["python", "pip", "git", "vscode"],
    "document":     ["nodejs", "npm", "mongodb", "git", "vscode"],
    "upload":       ["nodejs", "npm", "mongodb", "git", "vscode"],
    "filestorage":  ["nodejs", "npm", "mongodb", "docker", "git", "vscode"],
    "file-storage": ["nodejs", "npm", "mongodb", "docker", "git", "vscode"],
    "search":       ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],
    "urlshortener": ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],
    "url-shortener": ["nodejs", "npm", "mongodb", "redis", "git", "vscode"],
    "pastebin":     ["nodejs", "npm", "mongodb", "git", "vscode"],
    "notes":        ["nodejs", "npm", "mongodb", "git", "vscode"],
    "notepad":      ["nodejs", "npm", "git", "vscode"],
    "editor":       ["nodejs", "npm", "git", "vscode"],
    "codeeditor":   ["nodejs", "npm", "git", "vscode"],
    "ide":          ["nodejs", "npm", "typescript", "docker", "git", "vscode"],
}


# ══════════════════════════════════════════════════════════════════════════
#  LAYER 3 — Individual technology aliases → tool keys
# ══════════════════════════════════════════════════════════════════════════

TECH_ALIASES: dict[str, str] = {
    # Python
    "python": "python", "python3": "python", "py": "python", "python3.12": "python",
    "python3.11": "python311",
    "pip": "pip", "pip3": "pip",
    "pipenv": "pipenv", "poetry": "poetry", "uv": "uv",

    # JavaScript / TypeScript / runtimes
    "node": "nodejs", "nodejs": "nodejs", "node.js": "nodejs", "nodemon": "nodejs",
    "npm": "npm",
    "yarn": "yarn",
    "pnpm": "pnpm",
    "typescript": "typescript", "ts": "typescript", "tsc": "typescript",
    "deno": "deno",
    "bun": "bun",

    # JS frameworks (map to nodejs+npm since they install via npm)
    "react": "nodejs", "reactjs": "nodejs", "react.js": "nodejs",
    "angular": "nodejs", "angularjs": "nodejs", "angular.js": "nodejs",
    "vue": "nodejs", "vuejs": "nodejs", "vue.js": "nodejs",

    # Java ecosystem
    "java": "java", "jdk": "java", "openjdk": "java",
    "java17": "java17", "jdk17": "java17",
    "maven": "maven", "mvn": "maven",
    "gradle": "gradle",
    "kotlin": "kotlin", "kt": "kotlin",
    "scala": "scala",
    "groovy": "groovy",
    "clojure": "clojure", "clj": "clojure",

    # C / C++ / systems
    "gcc": "gcc", "c": "gcc",
    "g++": "gpp", "gpp": "gpp", "c++": "gpp", "cpp": "gpp",
    "clang": "clang", "llvm": "clang",
    "cmake": "cmake",
    "make": "make",
    "mingw": "mingw",
    "ninja": "ninja",
    "meson": "meson",

    # Rust
    "rust": "rust", "rustlang": "rust", "rs": "rust",
    "cargo": "cargo",
    "rustup": "rustup",

    # Go
    "go": "go", "golang": "go",

    # .NET
    "csharp": "csharp", "c#": "csharp",
    "fsharp": "fsharp", "f#": "fsharp",
    ".net": "dotnet", "dotnet": "dotnet",

    # Ruby
    "ruby": "ruby", "rb": "ruby",
    "gem": "gem", "rubygems": "gem",

    # PHP
    "php": "php", "php8": "php",
    "composer": "composer",

    # Dart / Flutter
    "dart": "dart",
    "flutter": "flutter",

    # Swift
    "swift": "swift",

    # Mobile
    "android": "android_sdk", "android-studio": "android_sdk",
    "react-native": "react_native", "reactnative": "react_native",

    # Databases
    "mongodb": "mongodb", "mongo": "mongodb",
    "mysql": "mysql", "mariadb": "mysql",
    "postgres": "postgres", "postgresql": "postgres", "pg": "postgres",
    "redis": "redis",
    "sqlite": "sqlite", "sqlite3": "sqlite",

    # DevOps
    "docker": "docker",
    "podman": "podman",
    "kubernetes": "kubernetes", "kubectl": "kubernetes", "k8s": "kubernetes",
    "helm": "helm",
    "terraform": "terraform", "tf": "terraform",
    "ansible": "ansible",
    "vagrant": "vagrant",
    "git": "git",
    "github": "gh_cli", "gh": "gh_cli",

    # Cloud
    "awscli": "aws_cli",
    "gcloud": "gcloud",
    "azure": "azure_cli", "az": "azure_cli",

    # AI / ML
    "tensorflow": "tensorflow",
    "pytorch": "pytorch", "torch": "pytorch",
    "cuda": "cuda",
    "anaconda": "anaconda", "conda": "anaconda",
    "miniconda": "miniconda",
    "jupyter": "jupyter", "notebook": "jupyter",

    # Editors / IDEs
    "vscode": "vscode", "code": "vscode", "vs-code": "vscode",
    "sublime": "sublime", "sublimetext": "sublime",
    "neovim": "neovim", "nvim": "neovim", "vim": "neovim",

    # Other languages
    "perl": "perl",
    "lua": "lua",
    "julia": "julia",
    "r": "r", "rlang": "r",
    "haskell": "haskell", "ghc": "haskell",
    "ocaml": "ocaml",
    "erlang": "erlang", "otp": "erlang",
    "elixir": "elixir",
    "zig": "zig",
    "nim": "nim",
    "crystal": "crystal",
    "prolog": "prolog", "swipl": "prolog",
    "racket": "racket",
    "solidity": "solidity", "sol": "solidity",
    "pascal": "pascal", "fpc": "pascal",

    # Build / tools
    "wsl": "wsl",
    "postman": "postman",
    "insomnia": "insomnia",
    "ngrok": "ngrok",
    "protobuf": "protobuf", "protoc": "protobuf",
    "ffmpeg": "ffmpeg",
    "curl": "curl",
    "wget": "wget",
    "jq": "jq",
}


@dataclass
class ParseResult:
    """Result of parsing a natural-language prompt."""

    matched_keys: list[str] = field(default_factory=list)
    matched_stack: str | None = None  # preset name if a stack was detected
    matched_domain: str | None = None  # problem domain if detected
    display_names: dict[str, str] = field(default_factory=dict)  # key → human name

    @property
    def has_results(self) -> bool:
        return len(self.matched_keys) > 0

    @property
    def label(self) -> str | None:
        """Human-readable label for what was matched."""
        if self.matched_stack:
            return self.matched_stack
        if self.matched_domain:
            return self.matched_domain
        return None


def _tokenize(prompt: str) -> list[str]:
    """Lowercase, strip punctuation, split into tokens."""
    text = prompt.lower().strip()
    # Normalise common separators
    text = text.replace(",", " ").replace(";", " ").replace("+", " ")
    tokens = re.findall(r"[a-z0-9_.#/+-]+", text)
    return tokens


def _strip_noise(tokens: list[str]) -> list[str]:
    """Remove noise / filler words (Hinglish and English)."""
    return [t for t in tokens if t not in _NOISE_WORDS]


def parse_prompt(prompt: str, available_tools: list[dict] | None = None) -> ParseResult:
    """Parse a natural-language prompt and return matching tool keys.

    Parameters
    ----------
    prompt : str
        The user's natural-language input (English or Hinglish).
    available_tools : list[dict] | None
        The loaded tools list from tools.json.  Used to build
        key → display-name mapping.  If *None*, display names
        default to the key itself.

    Returns
    -------
    ParseResult
        Contains the deduplicated list of tool keys to select.
    """
    result = ParseResult()
    if not prompt or not prompt.strip():
        return result

    # Build display name map from available tools
    name_map: dict[str, str] = {}
    valid_keys: set[str] = set()
    if available_tools:
        for tool in available_tools:
            key = tool.get("key", "")
            name_map[key] = tool.get("name", key)
            valid_keys.add(key)

    tokens = _tokenize(prompt)
    meaningful = _strip_noise(tokens)

    collected_keys: list[str] = []

    # Build n-grams for multi-word matching
    all_ngrams: list[str] = list(meaningful)
    for i in range(len(meaningful) - 1):
        all_ngrams.append(meaningful[i] + meaningful[i + 1])      # bigram no space
        all_ngrams.append(meaningful[i] + "-" + meaningful[i + 1])  # with hyphen

    # ── LAYER 1: Stack presets (highest priority) ───────────────────
    for ngram in all_ngrams:
        if ngram in STACK_PRESETS:
            result.matched_stack = ngram
            collected_keys.extend(STACK_PRESETS[ngram])

    # ── LAYER 2: Problem domains (if no stack matched) ──────────────
    if not result.matched_stack:
        for ngram in all_ngrams:
            if ngram in PROBLEM_DOMAINS:
                if result.matched_domain is None:
                    result.matched_domain = ngram
                collected_keys.extend(PROBLEM_DOMAINS[ngram])

    # ── LAYER 3: Individual tech aliases ────────────────────────────
    for token in meaningful:
        if token in TECH_ALIASES:
            collected_keys.append(TECH_ALIASES[token])

    # ── LAYER 4: Direct key match ───────────────────────────────────
    if valid_keys:
        for token in meaningful:
            if token in valid_keys:
                collected_keys.append(token)

    # Deduplicate while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for key in collected_keys:
        if key not in seen:
            if valid_keys and key not in valid_keys:
                continue
            seen.add(key)
            deduped.append(key)

    result.matched_keys = deduped
    result.display_names = {k: name_map.get(k, k) for k in deduped}

    return result
