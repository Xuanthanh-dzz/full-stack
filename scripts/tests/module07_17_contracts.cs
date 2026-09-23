using System.Reflection;
using System.Runtime.ExceptionServices;
using DynamicProgrammingDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static T Call<T>(string name,params object?[] args){try{return (T)typeof(Program).GetMethod(name,BindingFlags.NonPublic|BindingFlags.Static)!.Invoke(null,args)!;}catch(TargetInvocationException ex) when(ex.InnerException!=null){ExceptionDispatchInfo.Capture(ex.InnerException).Throw();throw;}}
 static void Main(){
var rng=new Random(717);for(int trial=0;trial<100;trial++){var coins=Enumerable.Range(0,4).Select(_=>rng.Next(1,12)).ToArray();int amount=rng.Next(60);var q=new Queue<(int Sum,int Steps)>();var seen=new HashSet<int>{0};q.Enqueue((0,0));int best=int.MaxValue;while(q.TryDequeue(out var state)){if(state.Sum==amount){best=state.Steps;break;}foreach(int c in coins){int next=state.Sum+c;if(next<=amount && seen.Add(next))q.Enqueue((next,state.Steps+1));}}Check(Call<int>("MinCoinsMemoized",coins,amount)==best && Call<int>("MinCoinsTabulated",coins,amount)==best,"BFS coin oracle");}foreach(var method in new[]{"MinCoinsMemoized","MinCoinsTabulated"}){Throws<ArgumentException>(()=>Call<int>(method,new[]{0},1));Throws<ArgumentOutOfRangeException>(()=>Call<int>(method,new[]{1},-1));}Throws<OverflowException>(()=>Call<int>("MinCoinsTabulated",new[]{1},int.MaxValue));
 }
}
