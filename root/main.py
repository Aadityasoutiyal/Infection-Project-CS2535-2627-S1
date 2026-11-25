import pygame
import random
import json
import csv
import os
import glob
import matplotlib.pyplot as plt


class Disease:
    def __init__(self, name: str, infectiousness: float, transmissibility: float,
                 lethality: float, recoverability: float, immunity_efficacy: float):
        self.name = name
        self.infectiousness = infectiousness
        self.transmissibility = transmissibility
        self.lethality = lethality
        self.recoverability = recoverability
        self.immunity_efficacy = immunity_efficacy


class MovementComponent:
    def __init__(self, x: float, y: float, speed: float, width: int, height: int):
        self.position = pygame.Vector2(x, y)
        angle = random.uniform(0, 360)
        self.velocity = pygame.Vector2(speed, 0).rotate(angle)
        self.width = width
        self.height = height

    def update(self, is_dead: bool) -> None:
        if is_dead:
            return
        self.position += self.velocity
        if self.position.x <= 0 or self.position.x >= self.width:
            self.velocity.x *= -1
        if self.position.y <= 0 or self.position.y >= self.height:
            self.velocity.y *= -1


class Person:
    def __init__(self, x: float, y: float, speed: float, width: int, height: int, disease: Disease):
        self.disease = disease
        self.movement = MovementComponent(x, y, speed, width, height)
        self.status = "susceptible"
        self.is_immune = False

    def update_movement(self) -> None:
        is_dead = (self.status == "dead")
        self.movement.update(is_dead)

    def check_infection_chance(self) -> bool:
        return random.uniform(0, 100) < self.disease.infectiousness

    def draw(self, surface: pygame.Surface) -> None:
        colors = {
            "susceptible": (100, 149, 237),
            "infected": (220, 20, 60),
            "recovered": (50, 205, 50),
            "dead": (128, 128, 128)
        }
        color = colors.get(self.status, (255, 255, 255))
        pygame.draw.circle(surface, color, (int(self.movement.position.x), int(self.movement.position.y)), 6)


class ImmunePerson(Person):
    def __init__(self, x: float, y: float, speed: float, width: int, height: int, disease: Disease):
        super().__init__(x, y, speed, width, height, disease)
        self.is_immune = True

    def check_infection_chance(self) -> bool:
        base_infected = super().check_infection_chance()
        if base_infected:
            if random.uniform(0, 100) < self.disease.immunity_efficacy:
                return False
            return True
        return False


def get_user_inputs():
    disease_name = input("Enter a disease name as a string that uniquely identifies the trial: ")
    population_count = int(input("Enter a population count as an integer: "))
    infectiousness = float(input("Enter infectiousness as a percentage chance of infection: "))
    transmissibility = float(input("Enter transmissibility as the distance infection can travel in pixels: "))
    lethality = float(input("Enter lethality as the percentage chance that an infected person dies on a given day: "))
    recoverability = float(
        input("Enter recoverability as the percentage chance that an infected person recovers on a given day: "))
    immunity = float(input("Enter immunity as the percentage of the population that is immune: "))
    immunity_efficacy = float(
        input("Enter immunity efficacy as the percentage chance that immunity prevents infection: "))
    return disease_name, population_count, infectiousness, transmissibility, lethality, recoverability, immunity, immunity_efficacy


def initialize_population(pop_count, immunity_pct, disease, width, height):
    population = []
    immune_count = int(pop_count * (immunity_pct / 100))
    for i in range(pop_count):
        x = random.uniform(20, width - 20)
        y = random.uniform(20, height - 20)
        speed = 2.0
        if i < immune_count:
            person = ImmunePerson(x, y, speed, width, height, disease)
        else:
            person = Person(x, y, speed, width, height, disease)
        population.append(person)

    if population:
        population[0].status = "infected"
    return population


def create_new_csv(disease_name):
    os.makedirs("data", exist_ok=True)
    csv_filename = f"data/{disease_name.replace(' ', '_')}_{random.randint(1000, 9999)}.csv"
    return csv_filename


def append_csv_row(csv_filename, day, counts, disease):
    file_exists = os.path.exists(csv_filename)
    with open(csv_filename, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["DiseaseName", "Infectiousness", "Transmissibility", "Lethality", "Recoverability",
                             "ImmunityEfficacy"])
            writer.writerow([disease.name, disease.infectiousness, disease.transmissibility, disease.lethality,
                             disease.recoverability, disease.immunity_efficacy])
            writer.writerow(["Day", "Susceptible", "Infected", "Recovered", "Dead"])
        writer.writerow([day, counts["susceptible"], counts["infected"], counts["recovered"], counts["dead"]])


def display_graph(csv_filename):
    days, susceptible, infected, recovered, dead = [], [], [], [], []
    with open(csv_filename, mode="r") as f:
        reader = csv.reader(f)
        rows = list(reader)
        data_start = False
        for row in rows:
            if len(row) > 0 and row[0] == "Day":
                data_start = True
                continue
            if data_start and len(row) >= 5:
                days.append(int(row[0]))
                susceptible.append(int(row[1]))
                infected.append(int(row[2]))
                recovered.append(int(row[3]))
                dead.append(int(row[4]))

    plt.figure(figsize=(8, 5))
    plt.plot(days, susceptible, label="Susceptible", color="cornflowerblue")
    plt.plot(days, infected, label="Infected", color="crimson")
    plt.plot(days, recovered, label="Recovered", color="limegreen")
    plt.plot(days, dead, label="Dead", color="gray")
    plt.xlabel("Simulation Days")
    plt.ylabel("Population Count")
    plt.title("Infection Simulation Results")
    plt.legend()
    plt.grid(True)
    plt.show()


def run_simulation(population, disease, day=0, csv_filename=None):
    pygame.init()
    width, height = 800, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(f"Infection Simulation - {disease.name}")
    clock = pygame.time.Clock()

    if not csv_filename:
        csv_filename = create_new_csv(disease.name)

    font = pygame.font.SysFont(None, 24)
    paused = False
    fast_forward = False
    running = True

    day_timer = 0
    day_duration = 3000

    while running:
        dt = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_f:
                    fast_forward = not fast_forward
                elif event.key == pygame.K_s:
                    state_data = {
                        "disease": {
                            "name": disease.name,
                            "infectiousness": disease.infectiousness,
                            "transmissibility": disease.transmissibility,
                            "lethality": disease.lethality,
                            "recoverability": disease.recoverability,
                            "immunity_efficacy": disease.immunity_efficacy
                        },
                        "day": day,
                        "csv_filename": csv_filename,
                        "population": [{"x": p.movement.position.x, "y": p.movement.position.y, "status": p.status, "is_immune": p.is_immune} for p in population]
                    }
                    os.makedirs("data", exist_ok=True)
                    json_path = f"data/{disease.name.replace(' ', '_')}_day{day}.json"
                    with open(json_path, "w") as jf:
                        json.dump(state_data, jf, indent=4)
                    print(f"Simulation saved to {json_path}")
                elif event.key == pygame.K_q:
                    running = False

        if not paused:
            multiplier = 5 if fast_forward else 1
            day_timer += dt * multiplier

            if day_timer >= day_duration:
                day_timer = 0
                day += 1

                for p in population:
                    if p.status == "infected":
                        roll = random.uniform(0, 100)
                        if roll < disease.lethality:
                            p.status = "dead"
                        elif roll < (disease.lethality + disease.recoverability):
                            p.status = "recovered"

                counts = {"susceptible": 0, "infected": 0, "recovered": 0, "dead": 0}
                for p in population:
                    counts[p.status] += 1

                append_csv_row(csv_filename, day, counts, disease)

                if counts["infected"] == 0:
                    print("Simulation ended: No active infections remaining.")
                    running = False

            for p in population:
                p.update_movement()

            for p1 in population:
                if p1.status == "infected":
                    for p2 in population:
                        if p2.status == "susceptible":
                            dist = p1.movement.position.distance_to(p2.movement.position)
                            if dist <= disease.transmissibility:
                                if p2.check_infection_chance():
                                    p2.status = "infected"

        screen.fill((30, 30, 30))
        for p in population:
            p.draw(screen)

        counts = {"susceptible": 0, "infected": 0, "recovered": 0, "dead": 0}
        for p in population:
            counts[p.status] += 1

        hud_text = f"Day: {day} | S: {counts['susceptible']} | I: {counts['infected']} | R: {counts['recovered']} | D: {counts['dead']}"
        text_surface = font.render(hud_text, True, (255, 255, 255))
        screen.blit(text_surface, (10, 10))

        if paused:
            paused_surf = font.render("PAUSED (Space to resume)", True, (255, 255, 0))
            screen.blit(paused_surf, (10, 40))

        pygame.display.flip()

    pygame.quit()
    if os.path.exists(csv_filename):
        display_graph(csv_filename)


def main():
    while True:
        print("\n--- INFECTION SIMULATION MENU ---")
        print("1. Run a new simulation")
        print("2. View previous data graph")
        print("3. Exit")
        choice = input("Enter your choice (1-3): ").strip()

        if choice == "1":
            name, pop, inf, trans, leth, rec, imm, eff = get_user_inputs()
            disease = Disease(name, inf, trans, leth, rec, eff)
            width, height = 800, 600
            population = initialize_population(pop, imm, disease, width, height)
            csv_file = create_new_csv(disease.name)
            run_simulation(population, disease, day=0, csv_filename=csv_file)
        elif choice == "2":
            files = glob.glob("data/*.csv")
            if not files:
                print("No previous CSV data found.")
            else:
                print("Available CSV files:")
                for idx, f in enumerate(files):
                    print(f"{idx+1}. {f}")
                try:
                    f_choice = int(input("Select file number to view graph: ")) - 1
                    if 0 <= f_choice < len(files):
                        display_graph(files[f_choice])
                except ValueError:
                    print("Invalid input.")
        elif choice == "3":
            print("Exiting simulation. Goodbye!")
            break
        else:
            print("Invalid choice. Please select 1, 2, or 3.")


if __name__ == "__main__":
    main()