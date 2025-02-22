#!/bin/bash
LES_RL_NETTYPE=${LES_RL_NETTYPE:-FFNN}
LES_RL_FREQ_A=${LES_RL_FREQ_A:-8}
LES_RL_N_TSIM=${LES_RL_N_TSIM:-20}
LES_RL_NBLOCK=${LES_RL_NBLOCK:-4}
LES_RL_GRIDACT=${LES_RL_GRIDACT:-0}
LES_RL_GRIDACTSETTINGS=${LES_RL_GRIDACTSETTINGS:-${LES_RL_GRIDACT}}
LES_RL_POLICY_KERNEL=${LES_RL_POLICY_KERNEL:-0}


LES_RL_EVALUATE=${LES_RL_EVALUATE:-0}
if [ ${LES_RL_EVALUATE} == 0 ] ; then
LES_RL_EVALUATE="RE065,RE076,RE088,RE103,RE120,RE140,RE163"
#LES_RL_EVALUATE="RE111"
#LES_RL_EVALUATE="RE060,RE065,RE070,RE076,RE082,RE088,RE095,RE103,RE111,RE120,RE130,RE140,RE151,RE163,RE176,RE190,RE205"
fi

# compile executable:
COMPILEDIR=${SMARTIES_ROOT}/../CubismUP_3D/makefiles
#SKIPMAKE=true
if [ ! -z "$LES_RL_BLOCKSIZE" ] ; then
blocksize=$LES_RL_BLOCKSIZE
echo "using blocksize" $blocksize
elif [ ${LES_RL_NBLOCK} == 8 ] ; then
blocksize=4
elif [ ${LES_RL_NBLOCK} == 4 ] ; then
blocksize=8
elif [ ${LES_RL_NBLOCK} == 2 ] ; then
blocksize=16
else
echo "ERROR "
exit 1
fi
echo "using blocksize" $blocksize
if [[ "${SKIPMAKE}" != "true" ]] ; then
make -C ${COMPILEDIR} clean
make -C ${COMPILEDIR} bs=${blocksize} accfft=false -j rlHIT
fi

# copy executable:
cp ${COMPILEDIR}/rlHIT ${RUNDIR}/exec

# write simulation settings files:
# NOTE: -nu and -energyInjectionRate (=eps) make no difference
# our main file samples a random Re and computes the appropriate nu and eps
# -cs, not used by RL, but nonzero to avoid warnings
# -tend, not used by RL, but chosen to be >> than timeout given by RL
cat <<EOF >${RUNDIR}/runArguments00.sh
./simulation -bpdx $LES_RL_NBLOCK -bpdy $LES_RL_NBLOCK -bpdz $LES_RL_NBLOCK \
-extentx 6.2831853072 -tend 50000 -dump2D 1 -dump3D 1 -tdump 0 -CFL 0.1 \
-BC_x periodic -BC_y periodic -BC_z periodic -initCond HITurbulence \
-spectralIC fromFit -sgs RLSM -cs 0.5 -spectralForcing 1 \
-RungeKutta23 1 -Advection3rdOder 0 -keepMomentumConstant 1 \
-nprocsx 1 -nprocsy 1 -nprocsz 1 \
-analysis HIT -tAnalysis 100 -nu 0.005 -energyInjectionRate 0.2 \
-RL_freqActions ${LES_RL_FREQ_A} -RL_nIntTperSim ${LES_RL_N_TSIM} \
-RL_gridPointAgents ${LES_RL_GRIDACT} -initCondFileTokens ${LES_RL_EVALUATE} \
-RL_policyKernel ${LES_RL_POLICY_KERNEL}
EOF

#copy target files
THISDIR=${SMARTIES_ROOT}/apps/MARL_LES
#cp ${THISDIR}/target_RK_${LES_RL_NBLOCK}blocks/*  ${RUNDIR}/
cp ${THISDIR}/target_RK512_BPD032/*  ${RUNDIR}/
#cp ${THISDIR}/target_RK512_BPD128/*  ${RUNDIR}/

#copy settings file
# 1) either FFNN or RNN
# 2) number of actions per grad steps affected by number of agents per sim
if [ ${LES_RL_GRIDACTSETTINGS} == 0 ] ; then
SETTINGSF=VRACER_LES_${LES_RL_NETTYPE}_${blocksize}bsize.json
cp ${THISDIR}/settings/${SETTINGSF} ${RUNDIR}/settings.json
else
SETTINGSF=VRACER_LES_${LES_RL_NETTYPE}GRID_${blocksize}bsize.json
cp ${THISDIR}/settings/${SETTINGSF} ${RUNDIR}/settings.json
fi

export MPI_RANKS_PER_ENV=1
export EXTRA_LINE_ARGS=" --appSettings runArguments00.sh --nStepPappSett 0 "

