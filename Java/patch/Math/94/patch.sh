#!/bin/bash

grep -rl "Dfp.mant" . | xargs sed -i 's/Dfp.mant/mant/g'
grep -rl "AbstractStepInterpolator.currentState" . | xargs sed -i 's/AbstractStepInterpolator.currentState/currentState/g'
grep -rl "AbstractStepInterpolator.interpolatedState" . | xargs sed -i 's/AbstractStepInterpolator.interpolatedState/interpolatedState/g'
grep -rl "AbstractStepInterpolator.interpolatedDerivatives" . | xargs sed -i 's/AbstractStepInterpolator.interpolatedDerivatives/interpolatedDerivatives/g'
grep -rl "AbstractEstimator.parameters" . | xargs sed -i 's/AbstractEstimator.parameters/parameters/g'
grep -rl "DirectSearchOptimizer.simplex" . | xargs sed -i 's/DirectSearchOptimizer.simplex/simplex/g'
grep -rl "MultistepStepInterpolator.previousT" . | xargs sed -i 's/MultistepStepInterpolator.previousT/previousT/g'
grep -rl "MultistepStepInterpolator.previousF" . | xargs sed -i 's/MultistepStepInterpolator.previousF/previousF/g'
grep -rl "MultistepIntegrator.previousF" . | xargs sed -i 's/MultistepIntegrator.previousF/previousF/g'
grep -rl "AbstractEstimator.jacobian" . | xargs sed -i 's/AbstractEstimator.jacobian/jacobian/g'
grep -rl "AbstractEstimator.measurements" . | xargs sed -i 's/AbstractEstimator.measurements/measurements/g'
grep -rl "AbstractLeastSquaresOptimizer.weightedResidualJacobian" . | xargs sed -i 's/AbstractLeastSquaresOptimizer.weightedResidualJacobian/weightedResidualJacobian/g'
grep -rl "AbstractLeastSquaresOptimizer.jacobian" . | xargs sed -i 's/AbstractLeastSquaresOptimizer.jacobian/jacobian/g'
grep -rl "AbstractScalarDifferentiableOptimizer.point" . | xargs sed -i 's/AbstractScalarDifferentiableOptimizer.point/point/g'

