#!/usr/bin/env python3
import argparse, subprocess, re, time

def getRunArguments(traindir):
  with open(traindir+'/runArguments00.sh', 'r') as f:
    data = f.read()
  print(data)
  return data

def findArgument(data, argumentName):
  return re.search('-{} '.format(argumentName)+r'(\w+)', data).group(1)

def findIfGridAgent(data):
  gridAgent = findArgument(data, 'RL_gridPointAgents')
  assert gridAgent in ['0', '1']
  return gridAgent

def findActFreq(data):
  actFreq = findArgument(data, 'RL_freqActions')
  assert actFreq in ['2', '4', '8', '16']
  return actFreq

def findBlockNum(data):
  blockNum = findArgument(data, 'bpdx')
  assert blockNum in ['2', '4', '8']
  return blockNum

def findPolicyKernel(data):
  try:
    blockNum = findArgument(data, 'RL_policyKernel')
    assert blockNum in ['0', '1']
    return blockNum
  except Exception as e:
    print('Exception "{}" occurred while scanning for "RL_policyKernel", defaulting to 0'.format(e))
    return '0'

def clean(dirn):
  subprocess.run('rm /u/caldana/smarties/runs/'+dirn+'/exec', shell=True)
  subprocess.run('rm /u/caldana/smarties/runs/'+dirn+'/*.dat', shell=True)
  subprocess.run('rm /u/caldana/smarties/runs/'+dirn+'/*.raw', shell=True)
  subprocess.run('rm /u/caldana/smarties/runs/'+dirn+'/invCovLogE_RE*', shell=True)
  subprocess.run('rm /u/caldana/smarties/runs/'+dirn+'/scalars_RE*', shell=True)
  subprocess.run('rm /u/caldana/smarties/runs/'+dirn+'/spectrumLogE_RE*', shell=True)
  subprocess.run('rm /u/caldana/smarties/runs/'+dirn+'/stdevLogE_RE*', shell=True)
  subprocess.run('rm /u/caldana/smarties/runs/'+dirn+'/simulation_000_00000/*.raw', shell=True)
  path = '/u/caldana/smarties/runs/'+dirn+'/simulation_000_00000'
  for ext in ['h5', 'xmf', 'status']:
    subprocess.run('find {} -name "*.{}" -type f -delete'.format(path, ext), shell=True)
  return

def launch(dirn, args, lastCompiledBlocksize):
  path = args.restartsPath +'/' + dirn
  data = getRunArguments(path)
  bGridAgents = int(findIfGridAgent(data))
  assert bGridAgents == 0
  BPD  = int(findBlockNum(data))
  BSIZE = 32 // BPD
  assert BPD * BSIZE == 32
  cmd = ''
  cmd = cmd + ' export LES_RL_N_TSIM=100    \n '
  cmd = cmd + ' export LES_RL_FREQ_A=%s     \n ' % findActFreq(data)
  cmd = cmd + ' export LES_RL_BLOCKSIZE=%d  \n ' % BSIZE
  cmd = cmd + ' export LES_RL_NBLOCK=%d     \n ' % BPD
  cmd = cmd + ' export SKIPMAKE=%s \n ' % str(lastCompiledBlocksize == BSIZE).lower()
  cmd = cmd + ' export LES_RL_GRIDACT=%d \n ' % bGridAgents
  cmd = cmd + ' export LES_RL_NETTYPE=FFNN \n '
  cmd = cmd + ' export LES_RL_GRIDACTSETTINGS=0 \n '
  cmd = cmd + ' export LES_RL_POLICY_KERNEL=%s \n ' % findPolicyKernel(data)
  common = ' smarties.py MARL_LES --nEvalEpisodes 2 --clockHours 1'\
           ' --nThreads {} {} '.format(args.nThreads, '--hpc {}'.format(args.hpc) if args.hpc else '')
  res = [60, 65, 70, 76, 82, 88, 95, 103, 111, 120, 130, 140, 151, 163, 176, 190, 205]
  for i, re in enumerate(res):
    cmdre = cmd + ' export LES_RL_EVALUATE=RE%03d \n ' % re
    runn = '%s_%03dPD_RE%03d' % (dirn, 32, re)
    runcmd = '%s %s -r %s --restart %s' % (cmdre, common, runn, path)
    print(runcmd)
    subprocess.run(runcmd, shell=True)
    if args.hpc:
      time.sleep(60*8)
      clean(runn)
    if i == 0: 
      cmd = cmd + ' export SKIPMAKE=true \n '
  return BSIZE

if __name__ == '__main__':
  parser = argparse.ArgumentParser(
    description = "Evaluate trained directories.")
  parser.add_argument('restarts', nargs='+',
                      help="Directories containing trained policy to evaluate")
  parser.add_argument('--restartsPath', default='../../runs/',
                      help="Optional path to trained dirs, if not default")
  parser.add_argument('--hpc', default="", help="HPC name")
  parser.add_argument('--nThreads', type=int, default=1)
  args = parser.parse_args()

  lastCompiledBlocksize = -1
  for dirn in args.restarts:
    lastCompiledBlocksize = launch(dirn, args, lastCompiledBlocksize)


