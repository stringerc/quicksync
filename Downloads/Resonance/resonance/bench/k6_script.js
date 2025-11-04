import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  thresholds: {
    http_req_duration: ['p(95)<400', 'p(99)<800'],
  },
  stages: [
    { duration: '30s', target: 50 },
    { duration: '2m', target: 200 },
    { duration: '30s', target: 0 },
  ],
  ext: {
    loadimpact: {
      projectID: 0,
    },
  },
};

export default function () {
  // Open-loop constant rate generation
  const r = Math.random();
  const path = r < 0.7 ? '/api/fast' : '/api/slow';

  http.get(`http://localhost:3000${path}`);

  // Uniform spacing (open-loop)
  sleep(1.0);
}

