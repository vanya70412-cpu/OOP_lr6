from dataclasses import dataclass
from enum import Enum
import pickle
import csv
import json
import os


class TaskPriority(Enum):
    LOW = "Низький"
    MEDIUM = "Середній"
    HIGH = "Високий"
    CRITICAL = "Критичний"


class TaskStatus(Enum):
    TODO = "Нове"
    IN_PROGRESS = "У роботі"
    DONE = "Виконано"


@dataclass
class Employee:
    emp_id: str
    full_name: str
    role: str
    hourly_rate: float


@dataclass
class Project:
    code: str
    title: str
    department: str


class Task:
    """Базовий клас завдання програмного проєкту."""

    def __init__(self, task_id: str, title: str, project: Project,
                 assignee: Employee, priority: TaskPriority,
                 base_hours: float, status: TaskStatus = TaskStatus.TODO):
        self.task_id = task_id
        self.title = title
        self.project = project
        self.assignee = assignee
        self.priority = priority
        self.base_hours = float(base_hours)
        self.status = status

    def estimate_hours(self) -> float:
        return round(self.base_hours, 1)

    def get_task_category(self) -> str:
        return "Загальне завдання"

    def get_info(self) -> str:
        return (
            f"[{self.task_id}] ({self.get_task_category()}) {self.title} | "
            f"Проєкт: {self.project.code} | Виконавець: {self.assignee.full_name} | "
            f"Пріоритет: {self.priority.value} | Статус: {self.status.value} | "
            f"Оцінка: {self.estimate_hours()} год"
        )


class DevelopmentTask(Task):
    """Клас завдання на розробку нової функціональності."""

    def __init__(self, task_id: str, title: str, project: Project,
                 assignee: Employee, priority: TaskPriority,
                 base_hours: float, complexity_coeff: float,
                 tech_stack: str, status: TaskStatus = TaskStatus.TODO):
        super().__init__(task_id, title, project, assignee, priority, base_hours, status)
        self.complexity_coeff = float(complexity_coeff)
        self.tech_stack = tech_stack

    def estimate_hours(self) -> float:
        return round(self.base_hours * self.complexity_coeff, 1)

    def get_task_category(self) -> str:
        return "Розробка (Dev)"


class BugTask(Task):
    """Клас завдання на виправлення дефекту (багу)."""

    def __init__(self, task_id: str, title: str, project: Project,
                 assignee: Employee, priority: TaskPriority,
                 base_hours: float, severity_level: int,
                 environment: str, status: TaskStatus = TaskStatus.TODO):
        super().__init__(task_id, title, project, assignee, priority, base_hours, status)
        self.severity_level = int(severity_level)
        self.environment = environment

    def estimate_hours(self) -> float:
        return round(self.base_hours + (self.severity_level * 1.5), 1)

    def get_task_category(self) -> str:
        return "Виправлення багу (Bug)"


class TestingTask(Task):
    """Клас завдання на перевірку якості та тестування (QA)."""

    def __init__(self, task_id: str, title: str, project: Project,
                 assignee: Employee, priority: TaskPriority,
                 base_hours: float, test_cases_count: int,
                 is_automated: bool, status: TaskStatus = TaskStatus.TODO):
        super().__init__(task_id, title, project, assignee, priority, base_hours, status)
        self.test_cases_count = int(test_cases_count)
        self.is_automated = bool(is_automated)

    def estimate_hours(self) -> float:
        factor = 0.15 if self.is_automated else 0.35
        return round(self.base_hours + (self.test_cases_count * factor), 1)

    def get_task_category(self) -> str:
        return "Тестування (QA)"


class ProjectManager:
    """Клас-менеджер для управління завданнями проєкту та файловою системою."""

    def __init__(self, config_path: str = "config.json"):
        self._tasks: list[Task] = []
        self.config_path = config_path
        self.config = {
            "company_name": "SoftLine Ukraine",
            "max_hours_limit": 80.0,
            "backup_file": "project_state.pkl",
            "report_file": "project_report.csv",
            "csv_delimiter": ";"
        }
        self.load_config(self.config_path)

    def load_config(self, filepath: str = "config.json") -> None:
        if not os.path.exists(filepath):
            self.save_config(filepath)
            print(f"[JSON] Створено базовий файл налаштувань '{filepath}'.")
            return
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                loaded_data = json.load(file)
                self.config.update(loaded_data)
            print(
                f"[JSON] Налаштування завантажено: компанія='{self.config['company_name']}', "
                f"ліміт трудомісткості={self.config['max_hours_limit']} год."
            )
        except (json.JSONDecodeError, OSError) as err:
            print(f"[Помилка JSON] Не вдалося прочитати '{filepath}': {err}")

    def save_config(self, filepath: str = "config.json") -> None:
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(self.config, file, ensure_ascii=False, indent=4)

    def add_task(self, task: Task) -> None:
        max_limit = float(self.config.get("max_hours_limit", 80.0))
        calc_hours = task.estimate_hours()
        if calc_hours > max_limit:
            raise ValueError(
                f"Оцінка часу ({calc_hours} год) перевищує ліміт з config.json ({max_limit} год)!"
            )
        self._tasks.append(task)
        print(f"[Успіх] Додано: {task.get_info()}")

    def show_all_tasks(self) -> None:
        print("\n" + "=" * 86)
        print(f" СПИСОК ЗАВДАНЬ ПРОЄКТУ ({self.config.get('company_name')}) — Всього: {len(self._tasks)}")
        print("=" * 86)
        if not self._tasks:
            print("  Колекція завдань порожня.")
        for item in self._tasks:
            print("  " + item.get_info())
        print("=" * 86)

    def save_system_state(self, filepath: str | None = None) -> None:
        target = filepath or self.config.get("backup_file", "project_state.pkl")
        with open(target, "wb") as file:
            pickle.dump(self._tasks, file)
        print(f"[Pickle] Стан системи ({len(self._tasks)} об'єктів) збережено у '{target}'.")

    def load_system_state(self, filepath: str | None = None) -> None:
        target = filepath or self.config.get("backup_file", "project_state.pkl")
        try:
            with open(target, "rb") as file:
                self._tasks = pickle.load(file)
            print(f"[Pickle] Успішно відновлено об'єктів із '{target}': {len(self._tasks)} шт.")
        except FileNotFoundError:
            print(f"[Помилка Pickle] Файл резервної копії '{target}' ще не створено.")
        except (pickle.UnpicklingError, EOFError) as err:
            print(f"[Помилка Pickle] Файл пошкоджено: {err}")

    def export_csv_report(self, filepath: str | None = None) -> None:
        target = filepath or self.config.get("report_file", "project_report.csv")
        delimiter = self.config.get("csv_delimiter", ";")
        with open(target, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file, delimiter=delimiter)
            writer.writerow([
                "ID завдання", "Категорія", "Назва завдання", "Код проєкту",
                "Виконавець", "Пріоритет", "Статус", "Трудомісткість (год)", "Вартість (грн)"
            ])
            for t in self._tasks:
                hours = t.estimate_hours()
                cost = round(hours * t.assignee.hourly_rate, 2)
                writer.writerow([
                    t.task_id, t.get_task_category(), t.title, t.project.code,
                    t.assignee.full_name, t.priority.value, t.status.value, hours, cost
                ])
        print(f"[CSV] Звіт успішно експортовано у '{target}' (записано рядків: {len(self._tasks)}).")


def run_cli() -> None:
    manager = ProjectManager()
    default_project = Project("PRJ-20", "CRM System v2.0", "Департамент розробки")
    emp_dev = Employee("E-01", "Коваленко О. І.", "Backend Developer", 650.0)
    emp_qa = Employee("E-02", "Мельник І. В.", "QA Engineer", 500.0)

    while True:
        print("\n--- МЕНЮ СИСТЕМИ УПРАВЛІННЯ ЗАВДАННЯМИ ПРОЄКТУ (ЛР №6) ---")
        print("1. Додати завдання на розробку (DevelopmentTask)")
        print("2. Додати завдання на виправлення багу (BugTask)")
        print("3. Додати завдання на тестування (TestingTask)")
        print("4. Переглянути всі завдання у пам'яті")
        print("5. Зберегти повний стан системи у бінарний файл (Pickle)")
        print("6. Відновити стан системи з бінарного файлу (Pickle)")
        print("7. Експортувати табличний звіт у файл (CSV)")
        print("8. Перечитати зовнішні налаштування (JSON)")
        print("0. Вийти з програми")
        choice = input("Ваш вибір (0-8): ").strip()

        try:
            if choice == "1":
                tid = input("ID завдання (напр. T-101): ").strip()
                title = input("Назва завдання: ").strip()
                hours = float(input("Базовий час (год): "))
                coeff = float(input("Коефіцієнт складності (напр. 1.5): "))
                stack = input("Технологічний стек (напр. Python/FastAPI): ").strip()
                task = DevelopmentTask(
                    tid, title, default_project, emp_dev,
                    TaskPriority.HIGH, hours, coeff, stack
                )
                manager.add_task(task)
            elif choice == "2":
                tid = input("ID багу (напр. B-202): ").strip()
                title = input("Опис дефекту: ").strip()
                hours = float(input("Базовий час усунення (год): "))
                sev = int(input("Рівень серйозності (1-5): "))
                env = input("Середовище (Prod/Stage): ").strip()
                task = BugTask(
                    tid, title, default_project, emp_dev,
                    TaskPriority.CRITICAL, hours, sev, env, TaskStatus.IN_PROGRESS
                )
                manager.add_task(task)
            elif choice == "3":
                tid = input("ID тестування (напр. Q-303): ").strip()
                title = input("Назва перевірки: ").strip()
                hours = float(input("Базовий час (год): "))
                cases = int(input("Кількість тест-кейсів: "))
                auto = input("Автоматизоване? (так/ні): ").strip().lower() == "так"
                task = TestingTask(
                    tid, title, default_project, emp_qa,
                    TaskPriority.MEDIUM, hours, cases, auto
                )
                manager.add_task(task)
            elif choice == "4":
                manager.show_all_tasks()
            elif choice == "5":
                manager.save_system_state()
            elif choice == "6":
                manager.load_system_state()
            elif choice == "7":
                manager.export_csv_report()
            elif choice == "8":
                manager.load_config()
            elif choice == "0":
                print("Роботу завершено.")
                break
            else:
                print("[Помилка] Оберіть пункт меню від 0 до 8.")
        except ValueError as err:
            print(f"[Помилка валідації даних]: {err}")


if __name__ == "__main__":
    run_cli()
