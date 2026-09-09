import React from 'react';
import { useWizard } from '../context/WizardContext';
import { StepIndicator } from '../components/StepIndicator';

import { Step1Source } from '../components/steps/Step1_Source';
import { Step2Videos } from '../components/steps/Step2_Videos';
import { Step3ClipMode } from '../components/steps/Step3_ClipMode';
import { Step4Config } from '../components/steps/Step4_Config';
import { Step5Summary } from '../components/steps/Step5_Summary';
import { Step6Processing } from '../components/steps/Step6_Processing';
import { Step7Complete } from '../components/steps/Step7_Complete';
import { Step8Download } from '../components/steps/Step8_Download';

export const WizardPage: React.FC = () => {
  const { step } = useWizard();

  return (
    <div className="w-full max-w-4xl mx-auto flex flex-col h-[calc(100vh-8rem)]">
      <StepIndicator />
      
      <div className="flex-1 mt-6 overflow-y-auto pb-12">
        {step === 1 && <Step1Source />}
        {step === 2 && <Step2Videos />}
        {step === 3 && <Step3ClipMode />}
        {step === 4 && <Step4Config />}
        {step === 5 && <Step5Summary />}
        {step === 6 && <Step6Processing />}
        {step === 7 && <Step7Complete />}
        {step === 8 && <Step8Download />}
      </div>
    </div>
  );
};
