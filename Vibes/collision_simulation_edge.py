import math

class ElasticCollisionSimulator:
    def __init__(self, m1, m2, v1_initial, v2_initial=0, wall_position=0, max_collisions=1000):
        """
        Event-driven elastic collision simulator with edge-based collision detection.
        """
        self.m1, self.m2 = m1, m2
        self.v1, self.v2 = v1_initial, v2_initial

        # Calculate block "radii" based on mass (volume ~ mass, so radius ~ mass^(1/3))
        self.r1 = self.get_radius(m1)
        self.r2 = self.get_radius(m2)

        # Positions (center of mass)
        self.x1 = 10.0   # Block 1 starts right
        self.x2 = 3.0    # Block 2 starts between block 1 and wall
        self.wall_pos = wall_position

        self.time = 0
        self.collision_count = 0
        self.max_collisions = max_collisions
        self.collision_log = []

    @staticmethod
    def get_radius(mass):
        """Calculate block radius from mass (radius ~ mass^(1/3) for constant density)."""
        return max(0.1, (mass / 1000) ** (1/3) * 0.5)

    def elastic_collision_blocks(self):
        """Calculate velocities after elastic collision between two blocks."""
        v1_new = ((self.m1 - self.m2) * self.v1 + 2 * self.m2 * self.v2) / (self.m1 + self.m2)
        v2_new = ((self.m2 - self.m1) * self.v2 + 2 * self.m1 * self.v1) / (self.m1 + self.m2)
        return v1_new, v2_new

    def elastic_collision_wall(self, velocity):
        """Calculate velocity after elastic collision with wall."""
        return -velocity

    def time_to_wall_collision(self):
        """Calculate time until block 1's edge hits the wall."""
        if self.v1 >= 0:  # Not moving toward wall
            return float('inf')
        # Left edge of block 1: x1 - r1
        # (x1 - r1) + v1*t = wall_pos
        # t = (wall_pos - (x1 - r1)) / v1
        return (self.wall_pos - (self.x1 - self.r1)) / self.v1

    def time_to_block_collision(self):
        """Calculate time until block edges touch."""
        if self.v1 >= self.v2:  # Not approaching
            return float('inf')
        # Right edge of block 2: x2 + r2
        # Left edge of block 1: x1 - r1
        # Collision when: x1 - r1 = x2 + r2
        # (x1 - r1) + v1*t = (x2 + r2) + v2*t
        # (v1 - v2)*t = (x2 + r2) - (x1 - r1)
        # t = ((x2 + r2) - (x1 - r1)) / (v1 - v2)
        if abs(self.v1 - self.v2) < 1e-15:
            return float('inf')
        t = ((self.x2 + self.r2) - (self.x1 - self.r1)) / (self.v1 - self.v2)
        return t if t > 1e-10 else float('inf')

    def time_to_wall_collision_block2(self):
        """Calculate time until block 2's edge hits the wall."""
        if self.v2 >= 0:  # Not moving toward wall
            return float('inf')
        # Left edge of block 2: x2 - r2
        # (x2 - r2) + v2*t = wall_pos
        # t = (wall_pos - (x2 - r2)) / v2
        return (self.wall_pos - (self.x2 - self.r2)) / self.v2

    def kinetic_energy(self):
        """Calculate total kinetic energy."""
        return 0.5 * self.m1 * self.v1**2 + 0.5 * self.m2 * self.v2**2

    def momentum(self):
        """Calculate total momentum."""
        return self.m1 * self.v1 + self.m2 * self.v2

    def run(self):
        """Run the full event-driven simulation."""
        print(f"\n{'='*80}")
        print(f"Elastic Collision Simulation (Edge-based Detection)")
        print(f"{'='*80}")
        print(f"Block 1 - Mass: {self.m1}, Radius: {self.r1:.3f}, Initial velocity: {self.v1}")
        print(f"Block 2 - Mass: {self.m2}, Radius: {self.r2:.3f}, Initial velocity: {self.v2}")
        print(f"Mass ratio (m1/m2): {self.m1/self.m2:.1f}")
        print(f"Wall position: {self.wall_pos}")
        print(f"{'='*80}\n")

        initial_ke = self.kinetic_energy()
        initial_momentum = self.momentum()

        while self.collision_count < self.max_collisions:
            # Check if blocks are moving
            if abs(self.v1) < 1e-10 and abs(self.v2) < 1e-10:
                print(f"Simulation stopped - all blocks at rest\n")
                break

            # Calculate time to next collision
            t_wall = self.time_to_wall_collision()
            t_blocks = self.time_to_block_collision()
            t_wall_2 = self.time_to_wall_collision_block2()

            # Determine which collision happens first
            if t_wall < t_blocks and t_wall < t_wall_2 and t_wall != float('inf'):
                # Wall collision (block 1)
                dt = t_wall
                self.x1 += self.v1 * dt
                self.x2 += self.v2 * dt
                self.time += dt
                self.x1 = self.wall_pos + self.r1

                self.v1 = self.elastic_collision_wall(self.v1)
                self.collision_count += 1

                ke = self.kinetic_energy()

                print(f"[Collision {self.collision_count}] t={self.time:.6f}s - WALL collision (block 1)")
                print(f"  Block 1 velocity: {self.v1:12.6f}")
                print(f"  Block 2 velocity: {self.v2:12.6f}")
                print(f"  KE: {ke:.6f} (diff: {abs(ke - initial_ke):.2e})")
                print()

                self.collision_log.append((self.time, "Wall", self.v1, self.v2))

            elif t_blocks != float('inf') and t_blocks < t_wall_2:
                # Block-to-block collision
                dt = t_blocks
                self.x1 += self.v1 * dt
                self.x2 += self.v2 * dt
                self.time += dt

                self.v1, self.v2 = self.elastic_collision_blocks()
                self.collision_count += 1

                ke = self.kinetic_energy()

                print(f"[Collision {self.collision_count}] t={self.time:.6f}s - BLOCK collision")
                print(f"  Block 1 velocity: {self.v1:12.6f}")
                print(f"  Block 2 velocity: {self.v2:12.6f}")
                print(f"  KE: {ke:.6f} (diff: {abs(ke - initial_ke):.2e})")
                print()

                self.collision_log.append((self.time, "Blocks", self.v1, self.v2))

            elif t_wall_2 != float('inf'):
                # Block 2 hits wall
                dt = t_wall_2
                self.x1 += self.v1 * dt
                self.x2 += self.v2 * dt
                self.time += dt
                self.x2 = self.wall_pos + self.r2

                self.v2 = self.elastic_collision_wall(self.v2)
                self.collision_count += 1

                ke = self.kinetic_energy()

                print(f"[Collision {self.collision_count}] t={self.time:.6f}s - WALL collision (block 2)")
                print(f"  Block 1 velocity: {self.v1:12.6f}")
                print(f"  Block 2 velocity: {self.v2:12.6f}")
                print(f"  KE: {ke:.6f} (diff: {abs(ke - initial_ke):.2e})")
                print()

                self.collision_log.append((self.time, "Wall-Block2", self.v1, self.v2))
            else:
                print("No more collisions possible\n")
                break

        print(f"{'='*80}")
        print(f"Total collisions: {self.collision_count}")
        print(f"Final time: {self.time:.6f}s")
        print(f"Final velocities - Block 1: {self.v1:.10f}, Block 2: {self.v2:.10f}")
        print(f"Final KE: {self.kinetic_energy():.10f}")
        print(f"Final Momentum: {self.momentum():.10f}")
        print(f"{'='*80}\n")

        return self.collision_count


# Test it
if __name__ == "__main__":
    print("\n" + "="*80)
    print("SIMULATION: Mass ratio 1:10000 (10000kg vs 1kg) - Edge-based collision")
    print("="*80)
    sim = ElasticCollisionSimulator(m1=10000, m2=1, v1_initial=-1)
    sim.run()
