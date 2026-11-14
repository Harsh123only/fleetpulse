# ⚡ FleetPulse — Real-Time Urban Logistics & AI Anomaly Engine

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django REST](https://img.shields.io/badge/Django_REST-092E20?style=for-the-badge&logo=django&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-231F20?style=for-the-badge&logo=apachekafka&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)

**FleetPulse** is a distributed, event-driven fleet telemetry and AI dispatch platform modeled after Berlin's quick-commerce and e-bike delivery ecosystems. It ingests high-frequency IoT GPS and battery telemetry streams, predicts live delivery ETAs using **Scikit-learn**, detects stalled or low-battery vehicles via **Isolation Forest**, and triggers asynchronous order rescues using **Celery & RabbitMQ**.

![FleetPulse Berlin Command Center](frontend/dashboard_preview.png)

---

## 🏗️ System Architecture

```mermaid
graph LR
    Sim[Berlin IoT Simulator] -->|POST /api/v1/telemetry| Flask[Flask Ingestion Microservice]
    Flask -->|Publish Stream| Kafka[(Apache Kafka / Stream Buffer)]
    Flask -->|Sub-5ms Geo State| Redis[(Redis In-Memory Cache)]
    Flask -->|Real-Time Inference| ML[Scikit-learn AI Engine]
    ML -->|Anomaly Flagged| Celery[Celery + RabbitMQ Worker]
    Celery -->|Haversine Nearest Rider| DB[(MySQL / Django ORM)]
    Django[Django REST Framework] <--> DB
    UI[Dark-Mode Berlin Command UI] -->|1.5s Live Poll| Flask