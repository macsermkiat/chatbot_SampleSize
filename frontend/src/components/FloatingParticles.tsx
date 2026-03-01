"use client";

import { memo } from "react";
import { motion } from "framer-motion";

interface FloatingParticlesProps {
  count?: number;
}

const PARTICLE_COLORS = [
  "#c9b890", // parchment-400
  "#c6952b", // gold-500
  "#b9a273", // parchment-500
  "#e6ad36", // gold-400
  "#ddd3b8", // parchment-300
];

function getParticleProps(index: number, total: number) {
  const angle = (index / total) * 2 * Math.PI;
  const radiusX = 38 + ((index * 7) % 24);
  const radiusY = 32 + ((index * 11) % 28);

  const left = 50 + Math.cos(angle) * radiusX;
  const top = 50 + Math.sin(angle) * radiusY;

  const size = 2 + (index % 3);
  const duration = 4 + (index % 5);
  const delay = (index * 0.4) % 3;
  const driftY = -8 - (index % 12);

  const opacityPeak =
    index % 3 === 0 ? 0.5 : index % 3 === 1 ? 0.35 : 0.22;

  return { left, top, size, duration, delay, driftY, opacityPeak };
}

function FloatingParticles({
  count = 12,
}: FloatingParticlesProps) {
  return (
    <div
      className="absolute inset-0 overflow-hidden pointer-events-none"
      aria-hidden="true"
    >
      {Array.from({ length: count }, (_, i) => {
        const { left, top, size, duration, delay, driftY, opacityPeak } =
          getParticleProps(i, count);
        const color = PARTICLE_COLORS[i % PARTICLE_COLORS.length];

        return (
          <motion.span
            key={i}
            className="absolute rounded-full"
            style={{
              left: `${left}%`,
              top: `${top}%`,
              width: size,
              height: size,
              backgroundColor: color,
            }}
            animate={{
              y: [0, driftY, 0],
              opacity: [0, opacityPeak, 0],
              scale: [0.6, 1, 0.6],
            }}
            transition={{
              duration,
              delay,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
        );
      })}
    </div>
  );
}

export default memo(FloatingParticles);
