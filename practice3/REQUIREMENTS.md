# Практика №3. Контейнеризация и деплой микросервисов в Kubernetes

## Инструменты

- Кластер: Minikube (драйвер Docker)
- Управление: kubectl.
- Контейнеризация: Docker
- Регистр образов: локальный реестр Minikube (minikube image load) или внешний (Docker Hub, GitHub Container Registry).

## Требования

- Каждый микросервис должен быть развёрнут в отдельном Deployment (минимум 1 реплика, рекомендуется 2 для фронтенда).
- Для каждого Deployment создан соответствующий Service типа ClusterIP.
- Настроен Ingress для доступа к API Gateway извне (например, `myapp.local`).
- Все конфигурационные параметры (URLы сервисов, пароли БД) вынесены в ConfigMap и/или Secret.
- Приложение должно быть полностью работоспособно после `kubectl apply -f k8s/`.
- Развёртывание базы данных (PostgreSQL, MySQL) в кластере с использованием StatefulSet и PersistentVolume.
- Настройка Horizontal Pod Autoscaler (HPA) на основе CPU.
- Использование Service Mesh (Linkerd или Istio) для наблюдения за трафиком.
- Автоматизация через GitOps (ArgoCD).

## Требования к стркуктуре:

- в папке `practice3/k8s/`:
  - `deployment-*.yaml` (для каждого сервиса)
  - `service-*.yaml` (для каждого сервиса)
  - `ingress.yaml`
  - При необходимости: `configmap.yaml`, `secret.yaml`, `pvc.yaml`, `statefulset.yaml`.

## Требования к документации

- Файл practice3/README.md с отчётом:
  - Список всех микросервисов и их образов.
  - Инструкцию по развёртыванию в Minikube (шаги).
  - Скриншоты (оставь место под скриншоты):
    - kubectl get pods,svc,ingress
    - Успешного curl-запроса к приложению через Ingress
    - Логов одного из подов (например, kubectl logs frontend-xxx)
  - описание StatefulSet, PersistentVolume, HPA, Service Mesh, GitOps (ArgoCD) и соответствующие манифесты.
- обновленный файл README.md в корне проекта:
  - Инструкцию по развёртыванию в Minikube (шаги)
  - описание развертывания

## Результат

- Папка practice3/k8s/ со всеми YAML-манифестами.
- Файл practice3/README.md.
