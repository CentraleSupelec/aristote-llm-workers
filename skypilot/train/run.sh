#!/bin/bash

set -e
cd ~/sky_workdir

if [ -z "$CONFIG" ]; then
    echo "The variable \$CONFIG is empty, make sure to set this variable to the desired configuration path"
    exit 1
fi

export SKYPILOT_NUM_NODES=$(echo "$SKYPILOT_NODE_IPS" | wc -l)
export PER_DEVICE_BATCH_SIZE=${PER_DEVICE_BATCH_SIZE:-8}
export MACRO_BATCH_SIZE=${MACRO_BATCH_SIZE:-64}
export MICRO_BATCH_SIZE=$(($PER_DEVICE_BATCH_SIZE * $SKYPILOT_NUM_NODES * $SKYPILOT_NUM_GPUS_PER_NODE))
export GRADIENT_ACCUMULATION_STEPS=$(($MACRO_BATCH_SIZE / $MICRO_BATCH_SIZE > 1 ? $MACRO_BATCH_SIZE / $MICRO_BATCH_SIZE : 1 ))
export MACRO_BATCH_SIZE=$(($MACRO_BATCH_SIZE > $MICRO_BATCH_SIZE ? $MACRO_BATCH_SIZE : $MICRO_BATCH_SIZE))

echo "Number of nodes: $SKYPILOT_NUM_NODES"
echo "Number of GPUs per node: $SKYPILOT_NUM_GPUS_PER_NODE"
echo "Macro batch size: $MACRO_BATCH_SIZE"
echo "Micro batch size: $MICRO_BATCH_SIZE"
echo "Per device batch size: $PER_DEVICE_BATCH_SIZE"
echo "Gradient accumulation steps: $GRADIENT_ACCUMULATION_STEPS"

docker run \
    --rm \
    --gpus all \
    --ipc=host \
    -v /home/gcpuser/.cache:/root/.cache \
    -v $(pwd):/workspace/ \
    --env-file .env \
    -t llm-core-gpu:dev \
    llm-core-cli finetune \
        -c $CONFIG \
        --data.config.train_batch_size $PER_DEVICE_BATCH_SIZE \
        --data.config.validation_batch_size $PER_DEVICE_BATCH_SIZE \
        --trainer.num_nodes $SKYPILOT_NUM_NODES \
        --trainer.accumulate_grad_batches $GRADIENT_ACCUMULATION_STEPS
