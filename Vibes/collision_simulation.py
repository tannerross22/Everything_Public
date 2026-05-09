import math

class ElasticCollisionSimulator:
    def __init__(self, m1, m2, v1_initial, v2_initial=0, wall_position=0, max_collisions=1000):
        """
        Event-driven elastic collision simulator.

        Args:
            m1: Mass of block 1 (heavy mass)
            m2: Mass of block 2 (light mass)
            v1_initial: Initial velocity of block 1 (negative = moving left)
            v2_initial: Initial velocity of block 2
            wall_position: Position of wall
            max_collisions: Maximum number of collisions to simulate
        """
        self.m1, self.m2 = m1, m2
        self.v1, self.v2 = v1_initial, v2_initial

        # Positions
        self.x1 = 10.0   # Block 1 starts right, moving left toward wall
        self.x2 = 3.0    # Block 2 starts between block 1 and wall
        self.wall_pos = wall_position

        self.time = 0
        self.collision_count = 0
        self.max_collisions = max_collisions
        self.collision_log = []
        self.velocity_log = []

    def elastic_collision_blocks(self):
        """Calculate velocities after elastic collision between two blocks."""
        v1_new = ((self.m1 - self.m2) * self.v1 + 2 * self.m2 * self.v2) / (self.m1 + self.m2)
        v2_new = ((self.m2 - self.m1) * self.v2 + 2 * self.m1 * self.v1) / (self.m1 + self.m2)
        return v1_new, v2_new

    def elastic_collision_wall(self, velocity):
        """Calculate velocity after elastic collision with wall."""
        return -velocity

    def time_to_wall_collision(self):
        """Calculate time until block 1 hits the wall."""
        if self.v1 >= 0:  # Not moving toward wall
            return float('inf')
        # x1 + v1*t = wall_pos
        # t = (wall_pos - x1) / v1
        return (self.wall_pos - self.x1) / self.v1

    def time_to_wall_collision_block2(self):
        """Calculate time until block 2 hits the wall."""
        if self.v2 >= 0:  # Not moving toward wall
            return float('inf')
        # x2 + v2*t = wall_pos
        # t = (wall_pos - x2) / v2
        return (self.wall_pos - self.x2) / self.v2

    def time_to_block_collision(self):
        """Calculate time until blocks collide."""
        if self.v1 >= self.v2:  # Not approaching
            return float('inf')
        # x1 + v1*t = x2 + v2*t
        # (v1 - v2)*t = x2 - x1
        # t = (x2 - x1) / (v1 - v2)
        if abs(self.v1 - self.v2) < 1e-15:
            return float('inf')
        t = (self.x2 - self.x1) / (self.v1 - self.v2)
        return t if t > 1e-10 else float('inf')

    def kinetic_energy(self):
        """Calculate total kinetic energy."""
        return 0.5 * self.m1 * self.v1**2 + 0.5 * self.m2 * self.v2**2

    def momentum(self):
        """Calculate total momentum."""
        return self.m1 * self.v1 + self.m2 * self.v2

    def run(self):
        """Run the full event-driven simulation."""
        print(f"\n{'='*80}")
        print(f"Elastic Collision Simulation (Event-Driven)")
        print(f"{'='*80}")
        print(f"Block 1 - Mass: {self.m1}, Initial velocity: {self.v1}")
        print(f"Block 2 - Mass: {self.m2}, Initial velocity: {self.v2}")
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
            t_wall_1 = self.time_to_wall_collision()
            t_blocks = self.time_to_block_collision()
            t_wall_2 = self.time_to_wall_collision_block2()

            # Determine which collision happens first
            if t_wall_1 < t_blocks and t_wall_1 < t_wall_2 and t_wall_1 != float('inf'):
                # Wall collision (block 1)
                dt = t_wall_1
                self.x1 += self.v1 * dt
                self.x2 += self.v2 * dt
                self.time += dt
                self.x1 = self.wall_pos

                self.v1 = self.elastic_collision_wall(self.v1)
                self.collision_count += 1

                ke = self.kinetic_energy()
                momentum = self.momentum()

                print(f"[Collision {self.collision_count}] t={self.time:.6f}s - WALL collision")
                print(f"  Block 1 velocity: {self.v1:12.6f}")
                print(f"  Block 2 velocity: {self.v2:12.6f}")
                print(f"  KE: {ke:.6f} (initial: {initial_ke:.6f}, diff: {abs(ke - initial_ke):.2e})")
                print(f"  Momentum: {momentum:.6f} (initial: {initial_momentum:.6f})")
                print()

                self.collision_log.append((self.time, "Wall", self.v1, self.v2))

            elif t_blocks != float('inf'):
                # Block-to-block collision
                dt = t_blocks
                self.x1 += self.v1 * dt
                self.x2 += self.v2 * dt
                self.time += dt

                self.v1, self.v2 = self.elastic_collision_blocks()
                self.collision_count += 1

                ke = self.kinetic_energy()
                momentum = self.momentum()

                print(f"[Collision {self.collision_count}] t={self.time:.6f}s - BLOCK collision")
                print(f"  Block 1 velocity: {self.v1:12.6f}")
                print(f"  Block 2 velocity: {self.v2:12.6f}")
                print(f"  KE: {ke:.6f} (initial: {initial_ke:.6f}, diff: {abs(ke - initial_ke):.2e})")
                print(f"  Momentum: {momentum:.6f} (initial: {initial_momentum:.6f})")
                print()

                self.collision_log.append((self.time, "Blocks", self.v1, self.v2))

            elif t_wall_2 != float('inf'):
                # Block 2 hits wall
                dt = t_wall_2
                self.x1 += self.v1 * dt
                self.x2 += self.v2 * dt
                self.time += dt
                self.x2 = self.wall_pos

                self.v2 = self.elastic_collision_wall(self.v2)
                self.collision_count += 1

                ke = self.kinetic_energy()
                momentum = self.momentum()

                print(f"[Collision {self.collision_count}] t={self.time:.6f}s - WALL collision (block 2)")
                print(f"  Block 1 velocity: {self.v1:12.6f}")
                print(f"  Block 2 velocity: {self.v2:12.6f}")
                print(f"  KE: {ke:.6f} (initial: {initial_ke:.6f}, diff: {abs(ke - initial_ke):.2e})")
                print(f"  Momentum: {momentum:.6f} (initial: {initial_momentum:.6f})")
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


# Test with different mass ratios
print("\n" + "="*80)
print("CONFIG 1: Block 2 between blocks and wall")
print("="*80)
print("\n" + "="*80)
print("SIMULATION 1A: Mass ratio 1:100 (1000kg vs 10kg)")
print("="*80)
sim1a = ElasticCollisionSimulator(m1=1000, m2=10, v1_initial=-1)
collisions1a = sim1a.run()

print("\n" + "="*80)
print("SIMULATION 1B: Mass ratio 1:10000 (10000kg vs 1kg)")
print("="*80)
sim1b = ElasticCollisionSimulator(m1=10000, m2=1, v1_initial=-1)
collisions1b = sim1b.run()

# Alternative: Block 2 starts at the wall
print("\n\n" + "="*80)
print("CONFIG 2: Block 2 starts AT the wall (different mass ratios)")
print("="*80)

class ElasticCollisionSimulator2(ElasticCollisionSimulator):
    def __init__(self, m1, m2, v1_initial, v2_initial=0, wall_position=0, max_collisions=1000):
        super().__init__(m1, m2, v1_initial, v2_initial, wall_position, max_collisions)
        # Block 2 starts at the wall
        self.x1 = 10.0
        self.x2 = 0.0  # At wall

print("\n" + "="*80)
print("SIMULATION 2A: Mass ratio 1:100 (1000kg vs 10kg), block 2 at wall")
print("="*80)
sim2a = ElasticCollisionSimulator2(m1=1000, m2=10, v1_initial=-1)
collisions2a = sim2a.run()

print("\n" + "="*80)
print("SIMULATION 2B: Mass ratio 1:10000 (10000kg vs 1kg), block 2 at wall")
print("="*80)
sim2b = ElasticCollisionSimulator2(m1=10000, m2=1, v1_initial=-1)
collisions2b = sim2b.run()

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Config 1 (block 2 between):")
print(f"  Mass ratio 100:1    -> {collisions1a} collisions")
print(f"  Mass ratio 10000:1  -> {collisions1b} collisions")
print(f"\nConfig 2 (block 2 at wall):")
print(f"  Mass ratio 100:1    -> {collisions2a} collisions")
print(f"  Mass ratio 10000:1  -> {collisions2b} collisions")
print("="*80)
