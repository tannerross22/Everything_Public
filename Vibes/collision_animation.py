import pygame
import math
from collision_simulation_edge import ElasticCollisionSimulator

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1600, 500
FPS = 60
WALL_POS = 50
SCALE = 20  # pixels per simulation unit

class CollisionAnimator:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Elastic Collision Simulator - Edge-Based Collision Detection")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 18)
        self.font_large = pygame.font.Font(None, 32)

        # Simulation parameters
        self.m1 = 10000
        self.m2 = 1
        self.v1_initial = -1
        self.sim = None
        self.trajectory = []

        self.running = True
        self.paused = False
        self.show_vectors = True
        self.show_energy = True
        self.show_grid = True
        self.playback_speed = 1.0
        self.playback_time = 0.0

        self.reset_simulation()

    def compute_full_trajectory(self):
        """Run the full simulation and record trajectory."""
        print(f"\nComputing trajectory for m1={self.m1}, m2={self.m2}...")

        self.trajectory = []
        sim = ElasticCollisionSimulator(
            m1=self.m1,
            m2=self.m2,
            v1_initial=self.v1_initial,
            wall_position=0,  # Wall is at position 0 in simulation
            max_collisions=5000
        )

        # Record initial state
        self.trajectory.append((sim.time, sim.x1, sim.x2, sim.v1, sim.v2, "start", sim.r1, sim.r2))

        # Run full simulation
        while sim.collision_count < sim.max_collisions:
            if abs(sim.v1) < 1e-10 and abs(sim.v2) < 1e-10:
                break

            t_wall = sim.time_to_wall_collision()
            t_blocks = sim.time_to_block_collision()
            t_wall_2 = sim.time_to_wall_collision_block2()

            min_times = [(t, "wall1") for t in [t_wall] if t != float('inf')]
            min_times += [(t, "blocks") for t in [t_blocks] if t != float('inf')]
            min_times += [(t, "wall2") for t in [t_wall_2] if t != float('inf')]

            if not min_times:
                break

            min_t, collision_type = min(min_times)

            # Execute collision
            if collision_type == "wall1":
                sim.x1 += sim.v1 * min_t
                sim.x2 += sim.v2 * min_t
                sim.time += min_t
                sim.x1 = sim.wall_pos + sim.r1
                sim.v1 = sim.elastic_collision_wall(sim.v1)
                collision_label = "wall1"

            elif collision_type == "blocks":
                sim.x1 += sim.v1 * min_t
                sim.x2 += sim.v2 * min_t
                sim.time += min_t
                sim.v1, sim.v2 = sim.elastic_collision_blocks()
                collision_label = "blocks"

            else:  # wall2
                sim.x1 += sim.v1 * min_t
                sim.x2 += sim.v2 * min_t
                sim.time += min_t
                sim.x2 = sim.wall_pos + sim.r2
                sim.v2 = sim.elastic_collision_wall(sim.v2)
                collision_label = "wall2"

            sim.collision_count += 1

            # Record position after collision
            self.trajectory.append((sim.time, sim.x1, sim.x2, sim.v1, sim.v2, collision_label, sim.r1, sim.r2))

        print(f"Computed {len(self.trajectory)} trajectory points")
        print(f"Total collisions: {sim.collision_count}")
        print(f"Total simulation time: {sim.time:.3f}s")
        print()

    def reset_simulation(self):
        """Create a new simulation with current parameters."""
        self.compute_full_trajectory()
        self.playback_time = 0.0

    def interpolate_state(self, t):
        """Get simulation state at time t by interpolating trajectory."""
        if not self.trajectory:
            return None

        if t <= self.trajectory[0][0]:
            return self.trajectory[0]

        if t >= self.trajectory[-1][0]:
            return self.trajectory[-1]

        # Find surrounding points
        for i in range(len(self.trajectory) - 1):
            t1, x1_1, x2_1, v1_1, v2_1, _, r1, r2 = self.trajectory[i]
            t2, x1_2, x2_2, v1_2, v2_2, _, _, _ = self.trajectory[i + 1]

            if t1 <= t <= t2:
                if t2 == t1:
                    return self.trajectory[i]

                # Linear interpolation
                alpha = (t - t1) / (t2 - t1)
                x1 = x1_1 + (x1_2 - x1_1) * alpha
                x2 = x2_1 + (x2_2 - x2_1) * alpha
                v1 = v1_1 + (v1_2 - v1_1) * alpha
                v2 = v2_1 + (v2_2 - v2_1) * alpha

                return (t, x1, x2, v1, v2, "interpolated", r1, r2)

        return self.trajectory[-1]

    def handle_input(self):
        """Handle keyboard and mouse input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.playback_time = 0.0
                elif event.key == pygame.K_v:
                    self.show_vectors = not self.show_vectors
                elif event.key == pygame.K_e:
                    self.show_energy = not self.show_energy
                elif event.key == pygame.K_g:
                    self.show_grid = not self.show_grid
                elif event.key == pygame.K_UP:
                    self.playback_speed = min(10.0, self.playback_speed + 0.5)
                elif event.key == pygame.K_DOWN:
                    self.playback_speed = max(0.1, self.playback_speed - 0.5)
                # Mass ratio controls
                elif event.key == pygame.K_1:
                    self.m2 = 1
                    self.reset_simulation()
                elif event.key == pygame.K_2:
                    self.m2 = 10
                    self.reset_simulation()
                elif event.key == pygame.K_3:
                    self.m2 = 100
                    self.reset_simulation()
                elif event.key == pygame.K_4:
                    self.m2 = 1000
                    self.reset_simulation()

    def draw(self):
        """Render the current state."""
        self.screen.fill((240, 240, 240))

        # Get current state
        state = self.interpolate_state(self.playback_time)
        if not state:
            return

        _, x1, x2, v1, v2, _, r1, r2 = state

        # Draw grid if enabled
        if self.show_grid:
            for i in range(0, WIDTH, 100):
                pygame.draw.line(self.screen, (220, 220, 220), (i, 0), (i, HEIGHT), 1)

        # Draw wall
        pygame.draw.line(self.screen, (0, 0, 0), (WALL_POS, 0), (WALL_POS, HEIGHT), 12)
        wall_label = self.font.render("WALL", True, (0, 0, 0))
        self.screen.blit(wall_label, (WALL_POS - 15, 10))

        # Center Y position
        center_y = HEIGHT // 2

        # Draw blocks
        x1_screen = WALL_POS + x1 * SCALE
        x2_screen = WALL_POS + x2 * SCALE
        r1_screen = r1 * SCALE
        r2_screen = r2 * SCALE

        # Block 1 (heavy) - Rectangle
        rect1 = pygame.Rect(x1_screen - r1_screen, center_y - r1_screen, 2 * r1_screen, 2 * r1_screen)
        pygame.draw.rect(self.screen, (50, 120, 200), rect1)
        pygame.draw.rect(self.screen, (0, 60, 150), rect1, 3)
        label1 = self.font.render(f"m1={self.m1}kg", True, (255, 255, 255))
        text_rect1 = label1.get_rect(center=rect1.center)
        self.screen.blit(label1, text_rect1)

        # Block 2 (light) - Rectangle
        rect2 = pygame.Rect(x2_screen - r2_screen, center_y - r2_screen, 2 * r2_screen, 2 * r2_screen)
        pygame.draw.rect(self.screen, (200, 50, 120), rect2)
        pygame.draw.rect(self.screen, (150, 0, 80), rect2, 3)
        label2 = self.font.render(f"m2={self.m2}kg", True, (255, 255, 255))
        text_rect2 = label2.get_rect(center=rect2.center)
        self.screen.blit(label2, text_rect2)

        # Draw velocity vectors if enabled
        if self.show_vectors:
            vel_scale = 100

            # Block 1 velocity
            if abs(v1) > 0.01:
                color = (50, 120, 200) if v1 < 0 else (0, 200, 50)
                start_x = x1_screen
                end_x = x1_screen + v1 * vel_scale
                pygame.draw.line(self.screen, color, (start_x, center_y - r1_screen - 20),
                               (end_x, center_y - r1_screen - 20), 3)
                # Arrowhead
                if v1 != 0:
                    arrow_len = 10
                    angle = 0 if v1 > 0 else math.pi
                    pygame.draw.line(self.screen, color, (end_x, center_y - r1_screen - 20),
                                   (end_x - arrow_len * math.cos(angle - 0.4), center_y - r1_screen - 20 - arrow_len * math.sin(angle - 0.4)), 3)
                    pygame.draw.line(self.screen, color, (end_x, center_y - r1_screen - 20),
                                   (end_x - arrow_len * math.cos(angle + 0.4), center_y - r1_screen - 20 - arrow_len * math.sin(angle + 0.4)), 3)
                vel_text1 = self.font.render(f"v1={v1:.3f}", True, color)
                self.screen.blit(vel_text1, (start_x - 30, center_y - r1_screen - 45))

            # Block 2 velocity
            if abs(v2) > 0.01:
                color = (200, 50, 120) if v2 < 0 else (0, 200, 50)
                start_x = x2_screen
                end_x = x2_screen + v2 * vel_scale
                pygame.draw.line(self.screen, color, (start_x, center_y + r2_screen + 20),
                               (end_x, center_y + r2_screen + 20), 3)
                # Arrowhead
                if v2 != 0:
                    arrow_len = 10
                    angle = 0 if v2 > 0 else math.pi
                    pygame.draw.line(self.screen, color, (end_x, center_y + r2_screen + 20),
                                   (end_x - arrow_len * math.cos(angle - 0.4), center_y + r2_screen + 20 - arrow_len * math.sin(angle - 0.4)), 3)
                    pygame.draw.line(self.screen, color, (end_x, center_y + r2_screen + 20),
                                   (end_x - arrow_len * math.cos(angle + 0.4), center_y + r2_screen + 20 - arrow_len * math.sin(angle + 0.4)), 3)
                vel_text2 = self.font.render(f"v2={v2:.3f}", True, color)
                self.screen.blit(vel_text2, (start_x - 30, center_y + r2_screen + 45))

        # Draw energy bar if enabled
        if self.show_energy:
            ke = 0.5 * self.m1 * v1**2 + 0.5 * self.m2 * v2**2
            initial_ke = 0.5 * self.m1 * self.v1_initial**2
            energy_bar_width = int(250 * (ke / initial_ke)) if initial_ke > 0 else 0
            pygame.draw.rect(self.screen, (100, 200, 100), (WIDTH - 270, 10, energy_bar_width, 25))
            pygame.draw.rect(self.screen, (0, 0, 0), (WIDTH - 270, 10, 250, 25), 2)
            energy_text = self.font.render(f"Energy: {ke:.1f}J", True, (0, 0, 0))
            self.screen.blit(energy_text, (WIDTH - 265, 30))

        # Draw info text (left side)
        y_offset = 10
        info_lines = [
            f"Mass Ratio: {self.m1}:{self.m2} ({self.m1/self.m2:.0f}:1)",
            f"Time: {self.playback_time:.4f}s / {self.trajectory[-1][0]:.4f}s" if self.trajectory else "Time: --",
            f"Playback Speed: {self.playback_speed:.1f}x",
            f"FPS: {self.clock.get_fps():.1f}",
        ]

        for line in info_lines:
            text = self.font.render(line, True, (0, 0, 0))
            self.screen.blit(text, (10, y_offset))
            y_offset += 22

        # Draw control info (bottom)
        y_offset = HEIGHT - 120
        controls = [
            "Controls: 1-4=Mass Ratio | SPACE=Pause | R=Reset | UP/DOWN=Speed",
            "V=Velocity Vectors | E=Energy Bar | G=Grid",
        ]
        for line in controls:
            text = self.font.render(line, True, (100, 100, 100))
            self.screen.blit(text, (10, y_offset))
            y_offset += 20

        # Pause indicator
        if self.paused:
            pause_text = self.font_large.render("PAUSED", True, (255, 0, 0))
            text_rect = pause_text.get_rect(center=(WIDTH // 2, 50))
            self.screen.blit(pause_text, text_rect)

        pygame.display.flip()

    def run(self):
        """Main animation loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            self.handle_input()

            if not self.paused and self.trajectory:
                self.playback_time += dt * self.playback_speed

                # Loop at end
                if self.playback_time > self.trajectory[-1][0]:
                    self.playback_time = self.trajectory[-1][0]

            self.draw()

        pygame.quit()

if __name__ == "__main__":
    animator = CollisionAnimator()
    animator.run()
