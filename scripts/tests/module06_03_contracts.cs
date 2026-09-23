using CompositionDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static void Main(){

 var log=new List<string>();var channel=new Probe(2);var outer=new LoggingChannel(new RetryingChannel(channel,3),log);
 Check(outer.Send("a","b") && channel.Calls==3 && log.Count==1,"outer log");
 log.Clear();channel=new Probe(2);Check(new RetryingChannel(new LoggingChannel(channel,log),3).Send("a","b") && log.Count==3,"inner log");
 var first=new Probe(0);var second=new Probe(0);Check(new CompositeChannel(first,second).Send("a","b") && second.Calls==1,"fanout not short-circuit");
 var bad=new Probe(10);Check(!new RetryingChannel(bad,2).Send("a","b") && bad.Calls==2,"attempt budget");
 var fault=new Fault();log.Clear();Throws<IOException>(()=>new LoggingChannel(new RetryingChannel(fault,3),log).Send("a","b"));Check(fault.Calls==1 && log.Count==0,"exception not retry/logged as success");

 }

 sealed class Probe(int failures):INotificationChannel {public int Calls;public string Name=>"probe";public bool Send(string r,string m)=>++Calls>failures;}
 sealed class Fault:INotificationChannel {public int Calls;public string Name=>"fault";public bool Send(string r,string m){Calls++;throw new IOException();}}

}
