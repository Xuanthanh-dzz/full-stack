using System.Reflection;
using System.Runtime.ExceptionServices;
using PriorityQueueDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static T Call<T>(string name,params object?[] args){try{return (T)typeof(Program).GetMethod(name,BindingFlags.NonPublic|BindingFlags.Static)!.Invoke(null,args)!;}catch(TargetInvocationException ex) when(ex.InnerException!=null){ExceptionDispatchInfo.Capture(ex.InnerException).Throw();throw;}}
 static void Main(){
var q=new PriorityQueue<SupportTicket,int>();var rng=new Random(78);var priorities=new List<int>();for(int i=0;i<100;i++){int p=rng.Next(5);priorities.Add(p);Call<object?>("Enqueue",q,new SupportTicket(i.ToString(),"test",p));}var ids=new HashSet<string>();var actual=new List<int>();while(q.TryDequeue(out var t,out int p)){Check(ids.Add(t.Id) && t.Priority==p,"no loss or priority mismatch");actual.Add(p);}Check(actual.SequenceEqual(priorities.Order()),"priority order without tie promise");
 }
}
