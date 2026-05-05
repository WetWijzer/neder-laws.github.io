import { reconcilePythonLogicInventory, reviewAcceptedLogicParity } from './pythonLogicInventory';

describe('reconcilePythonLogicInventory', () => {
  it('captures the selected 269-to-253 inventory reconciliation', () => {
    const reconciliation = reconcilePythonLogicInventory();

    expect(reconciliation).toMatchObject({
      pythonInventoryFiles: 269,
      typescriptWasmImplementationFiles: 253,
      uncoveredPythonFiles: 16,
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(reconciliation.tasks).toHaveLength(6);
    expect(reconciliation.tasks.reduce((total, task) => total + task.uncoveredFiles, 0)).toBe(16);
  });

  it('keeps uncovered behavior tasks browser-native and fail-closed', () => {
    const reconciliation = reconcilePythonLogicInventory();

    for (const task of reconciliation.tasks) {
      expect(task.task).toMatch(/TypeScript|WASM|browser|local/);
      expect(task.browserNative).toBe(true);
      expect(task.serverCallsAllowed).toBe(false);
      expect(task.pythonRuntimeAllowed).toBe(false);
    }
  });
});

describe('reviewAcceptedLogicParity', () => {
  it('maps accepted work evidence back to the browser-native port goal', () => {
    const review = reviewAcceptedLogicParity();

    expect(review).toMatchObject({
      reviewedAgainstGoal: 'browser-native TypeScript/WASM logic port',
      acceptedEvidenceCount: 5,
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(review.evidence.map((item) => item.area)).toEqual(
      expect.arrayContaining([
        'FOL and spaCy-style NLP extraction',
        'ML confidence scoring',
        'ZKP and verifier surfaces',
      ]),
    );
  });

  it('keeps missing parity tasks explicit when accepted-work evidence is absent', () => {
    const review = reviewAcceptedLogicParity();

    expect(review.missingParityTasks).toHaveLength(6);
    expect(review.missingParityTasks.reduce((total, task) => total + task.uncoveredFiles, 0)).toBe(
      16,
    );
    for (const evidence of review.evidence) {
      expect(evidence.acceptedWorkEvidence).toMatch(/^2026/);
      expect(evidence.runtimeFiles.length).toBeGreaterThan(0);
      expect(evidence.validationFiles.length).toBeGreaterThan(0);
      expect(evidence.serverCallsAllowed).toBe(false);
      expect(evidence.pythonRuntimeAllowed).toBe(false);
    }
  });
});
